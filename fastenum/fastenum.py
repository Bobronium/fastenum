from enum import (
    EnumMeta,
    Enum,
    Flag,
    IntFlag,
    _make_class_unpicklable,
    _high_bit,
    _power_of_two)

__all__ = ('enable', 'disable', 'enabled')


def _get_all_subclasses(cls):
    all_subclasses = set()
    for subclass in cls.__subclasses__():
        all_subclasses.add(subclass)
        all_subclasses.update(_get_all_subclasses(subclass))

    return all_subclasses


BUILTIN_ENUMS = _get_all_subclasses(Enum)

enabled = False


def enable():
    """
    Patches enum for best performance

    :param reload_modules: whether to reload modules after patch or not
    :param exclude_modules: set of modules which will not be reloaded
    :param frame_to_check: frame globals of which will be checked for imported enums (set 0 to skip check)
    """
    global enabled
    if enabled:
        raise RuntimeError('Builtin enum is already patched')

    patch: PatchMeta
    for patch in Patch.__subclasses__():
        patch.enable()

    for e in BUILTIN_ENUMS:
        for member in e._member_map_.values():
            object.__setattr__(member, 'name', member._name_)
            object.__setattr__(member, 'value', member._value_)
            object.__setattr__(
                member,
                '_unique_members_',
                {k: v for v, k in member._value2member_map_.items() if k in member._member_map_}
            )

    enabled = True


def disable():
    """
    Opposite of enable()
    """
    global enabled

    if not enabled:
        raise RuntimeError('Builtin enum was not patched')

    patch: PatchMeta
    for patch in Patch.__subclasses__():
        patch.disable()

    enabled = False


class PatchMeta(type):

    def __new__(mcs, name, bases, namespace):
        type_to_patch = namespace.pop('__target__', None)
        if type_to_patch is None:
            return type.__new__(mcs, name, bases, {})

        attrs_to_delete = namespace.pop('__attrs_to_delete__', set())
        del namespace['__module__']
        del namespace['__qualname__']

        original_attrs = {
            attr: type_to_patch.__dict__[attr]
            for attr in namespace.keys() | attrs_to_delete
            if attr in type_to_patch.__dict__
        }

        cls = type.__new__(mcs, name, bases, {})

        cls.__target__ = type_to_patch
        cls.__attrs_to_patch__ = namespace
        cls.__original_attrs__ = original_attrs
        cls.__attrs_to_delete__ = attrs_to_delete
        cls.__subclass_attrs__ = {}
        cls.enabled = False
        return cls

    def enable(cls):
        target = cls.__target__
        if not issubclass(target, type):
            subclasses = _get_all_subclasses(target)
        else:
            subclasses = set()

        for attr in cls.__attrs_to_delete__:
            delattr(target, attr)
            old_value = getattr(target, attr, None)
            for sub_cls in subclasses:
                try:
                    if getattr(sub_cls, attr) is old_value:
                        delattr(sub_cls, attr)
                except AttributeError:
                    pass

        for attr, new_value in cls.__attrs_to_patch__.items():
            try:
                old_value = getattr(target, attr)
            except AttributeError:
                continue
            else:
                cls.__original_attrs__[attr] = old_value
                for sub_cls in subclasses:
                    if getattr(sub_cls, attr) is old_value:
                        setattr(sub_cls, attr, new_value)
                        cls.__subclass_attrs__.setdefault(attr, set()).add(sub_cls)
            finally:
                setattr(target, attr, new_value)

        cls.enabled = True

    def disable(cls):
        target = cls.__target__
        for attr, value in cls.__original_attrs__.items():
            setattr(target, attr, value)
            for sub_cls in cls.__subclass_attrs__.get(attr, ()):
                setattr(sub_cls, attr, value)

        cls.enabled = False


class Patch(metaclass=PatchMeta):
    ...


class PatchedEnumMeta(Patch):
    __target__ = EnumMeta
    __attrs_to_delete__ = {'__getattr__'}

    def __new__(mcs, cls_name, bases, namespace):
        # an Enum class is final once enumeration items have been defined; it
        # cannot be mixed with other types (int, float, etc.) if it has an
        # inherited __new__ unless a new __new__ is defined (or the resulting
        # class will fail).
        #
        # remove any keys listed in _ignore_
        namespace.setdefault('_ignore_', []).append('_ignore_')
        ignore = namespace['_ignore_']
        for key in ignore:
            namespace.pop(key, None)
        member_type, first_enum = mcs._get_mixins_(bases)
        __new__, save_new, use_args = mcs._find_new_(namespace, member_type, first_enum)
        # save enum items into separate mapping so they don't get baked into
        # the new class
        enum_members = {k: namespace.pop(k) for k in namespace._member_names}

        # check for illegal enum names (any others?)
        invalid_names = enum_members.keys() & {'mro', ''}
        if invalid_names:
            raise ValueError('Invalid enum member name: {0}'.format(
                ','.join(invalid_names)))

        # create a default docstring if one has not been provided
        namespace.setdefault('__doc__', 'An enumeration.')

        # Try to move our enum names in __slots__ for fastest lookups,
        # However it won't work when enum is subclass of built-in type
        if enum_members:
            slots = set(namespace.get('__slots__', ())) | {'name', 'value', '_value_', '_name_'} ^ enum_members.keys()
            namespace['__slots__'] = slots
        try:
            cls = type.__new__(mcs, cls_name, bases, namespace)
        except TypeError:
            namespace.pop('__slots__')
            cls = type.__new__(mcs, cls_name, bases, namespace)

        cls._member_names_ = []  # names in definition order
        cls._member_map_ = {}  # name->value map
        cls._unique_members_ = {}  # name -> value map, but with unique values
        cls._member_type_ = member_type

        # Reverse value->name map for hashable values.
        cls._value2member_map_ = {}

        # If a custom type is mixed into the Enum, and it does not know how
        # to pickle itself, pickle.dumps will succeed but pickle.loads will
        # fail.  Rather than have the error show up later and possibly far
        # from the source, sabotage the pickle protocol for this class so
        # that pickle.dumps also fails.
        #
        # However, if the new class implements its own __reduce_ex__, do not
        # sabotage -- it's on them to make sure it works correctly.  We use
        # __reduce_ex__ instead of any of the others as it is preferred by
        # pickle over __reduce__, and it handles all pickle protocols.
        if '__reduce_ex__' not in namespace:
            if member_type is not object:
                methods = ('__getnewargs_ex__', '__getnewargs__', '__reduce_ex__', '__reduce__')
                if not any(m in member_type.__dict__ for m in methods):
                    _make_class_unpicklable(cls)

        # instantiate them, checking for duplicates as we go
        # we instantiate first instead of checking for duplicates first in case
        # a custom __new__ is doing something funky with the values -- such as
        # auto-numbering ;)
        for member_name in namespace._member_names:
            value = enum_members[member_name]
            if not isinstance(value, tuple):
                args = (value,)
            else:
                args = value
            if member_type is tuple:  # special case for tuple enums
                args = (args,)  # wrap it one more time
            if not use_args:
                enum_member = __new__(cls)
                if not hasattr(enum_member, '_value_'):
                    enum_member._value_ = value
            else:
                enum_member = __new__(cls, *args)
                if not hasattr(enum_member, '_value_'):
                    if member_type is object:
                        enum_member._value_ = value
                    else:
                        enum_member._value_ = value = member_type(*args)
                else:
                    value = enum_member._value_

            # rewriting Built-in Enum name and value properties
            object.__setattr__(enum_member, '_name_', member_name)
            object.__setattr__(enum_member, 'name', member_name)
            object.__setattr__(enum_member, 'value', value)

            enum_member.__objclass__ = cls
            enum_member.__init__(*args)
            # If another member with the same value was already defined, the
            # new becomes an alias to the existing one.
            for name, canonical_member in cls._member_map_.items():
                if canonical_member._value_ == enum_member._value_:
                    enum_member = canonical_member
                    break
            else:
                # Aliases don't appear in member names (only in __members__).
                cls._member_names_.append(member_name)
                cls._unique_members_[member_name] = enum_member

            # set attr directly to cls.__dict__ and add to _member_map_
            setattr(cls, member_name, enum_member)
            cls._member_map_[member_name] = enum_member
            try:
                # This may fail if value is not hashable. We can't add the value
                # to the map, and by-value lookups for this value will be
                # linear.
                cls._value2member_map_[value] = enum_member
            except TypeError:
                pass

        # double check that repr and friends are not the mixin's or various
        # things break (such as pickle)
        for name in ('__repr__', '__str__', '__format__', '__reduce_ex__'):
            class_method = getattr(cls, name)
            obj_method = getattr(member_type, name, None)
            enum_method = getattr(first_enum, name, None)
            if obj_method is not None and obj_method is class_method:
                setattr(cls, name, enum_method)

        # replace any other __new__ with our own (as long as Enum is not None,
        # anyway) -- again, this is to support pickle
        if Enum is not None:
            # if the user defined their own __new__, save it before it gets
            # clobbered in case they subclass later
            if save_new:
                cls.__new_member__ = __new__
            cls.__new__ = Enum.__new__

        return cls

    def __iter__(cls):
        return iter(cls._unique_members_.values())


class PatchedEnum(Patch):
    __target__ = Enum
    __attrs_to_delete__ = {'name', 'value'}

    def __new__(cls, value):
        """
        All enum instances are actually created during class construction
        without calling this method; this method is called by the metaclass'
        __call__ (i.e. Color(3) ), and by pickle

        Remove SLOW check of _missing_ returns, so it can return invalid Enum!
        """
        # by-value search for a matching enum member
        # see if it's in the reverse mapping (for hashable values)
        try:
            return cls._value2member_map_[value]
        except KeyError:
            if type(value) is cls:
                # moved it here in favor of faster lookups by value
                return value
        except TypeError:
            # not there, now do long search -- O(n) behavior
            for member in cls._member_map_.values():
                if member._value_ == value:
                    return member

        # set member name and value
        possible_member = cls._missing_(value)
        if possible_member is None:
            raise ValueError("%r is not a valid %s" % (value, cls.__name__))
        elif hasattr(possible_member, '_name_') and hasattr(possible_member, '_value_'):
            object.__setattr__(possible_member, 'value', possible_member._value_)
            object.__setattr__(possible_member, 'name', possible_member._name_)
        return possible_member

    def __setattr__(self, key, value):
        if key in {'name', 'value'}:
            raise AttributeError("Can't set attribute")
        object.__setattr__(self, key, value)

    def __delattr__(self, key):
        if key in {'name', 'value'}:
            raise AttributeError("Can't del attribute")
        object.__delattr__(self, key)

    @classmethod
    def __is_fast__(cls):
        return enabled


class PatchedFlag(Patch):
    __target__ = Flag

    @classmethod
    def _create_pseudo_member_(cls, value):
        """
        Create a composite member iff value contains only members.
        """
        pseudo_member = cls._value2member_map_.get(value, None)
        if pseudo_member is None:
            # verify all bits are accounted for
            _, extra_flags = _decompose(cls, value)
            if extra_flags:
                raise ValueError("%r is not a valid %s" % (value, cls.__name__))
            # construct a singleton enum pseudo-member
            pseudo_member = object.__new__(cls)
            pseudo_member._name_ = None
            pseudo_member._value_ = value
            # use setdefault in case another thread already created a composite
            # with this value
            pseudo_member = cls._value2member_map_.setdefault(value, pseudo_member)
            object.__setattr__(pseudo_member, 'value', pseudo_member._value_)
            object.__setattr__(pseudo_member, 'name', pseudo_member._name_)
        return pseudo_member


class PatchedIntFlag(Patch):
    __target__ = IntFlag

    @classmethod
    def _create_pseudo_member_(cls, value):
        pseudo_member = cls._value2member_map_.get(value, None)
        if pseudo_member is None:
            need_to_create = [value]
            # get unaccounted for bits
            _, extra_flags = _decompose(cls, value)
            # timer = 10
            while extra_flags:
                # timer -= 1
                bit = _high_bit(extra_flags)
                flag_value = 2 ** bit
                if (flag_value not in cls._value2member_map_ and
                        flag_value not in need_to_create
                ):
                    need_to_create.append(flag_value)
                if extra_flags == -flag_value:
                    extra_flags = 0
                else:
                    extra_flags ^= flag_value
            for value in reversed(need_to_create):
                # construct singleton pseudo-members
                pseudo_member = int.__new__(cls, value)
                pseudo_member._name_ = None
                pseudo_member._value_ = value
                object.__setattr__(pseudo_member, 'value', value)
                object.__setattr__(pseudo_member, 'name', None)
                # use setdefault in case another thread already created a composite
                # with this value
                pseudo_member = cls._value2member_map_.setdefault(value, pseudo_member)
        return pseudo_member


def _decompose(flag, value):
    """Extract all members from the value."""
    # _decompose is only called if the value is not named
    not_covered = value
    negative = value < 0
    # issue29167: wrap accesses to _value2member_map_ in a list to avoid race
    #             conditions between iterating over it and having more pseudo-
    #             members added to it
    if negative:
        # only check for named flags
        flags_to_check = [
            (m, v)
            for v, m in flag._value2member_map_.copy().items()
            if m.name is not None
        ]
    else:
        # check for named flags and powers-of-two flags
        flags_to_check = [
            (m, v)
            for v, m in flag._value2member_map_.copy().items()
            if m.name is not None or _power_of_two(v)
        ]
    members = []
    for member, member_value in flags_to_check:
        if member_value and member_value & value == member_value:
            members.append(member)
            not_covered &= ~member_value

    if not members and value in flag._value2member_map_:
        members.append(flag._value2member_map_[value])
    members.sort(key=lambda m: m._value_, reverse=True)
    if len(members) > 1 and members[0].value == value:
        # we have the breakdown, don't need the value member itself
        members.pop(0)
    return members, not_covered


enable()
