from enum import (
    EnumMeta,
    Enum,
    _make_class_unpicklable,
    _high_bit,
)
from typing import MutableMapping


def _get_all_subclasses(cls):
    all_subclasses = set()
    for subclass in type.__subclasses__(cls):
        all_subclasses.add(subclass)
        all_subclasses.update(_get_all_subclasses(subclass))

    return all_subclasses


class _Missing:
    def __repr__(self):
        return "< 'MISSING' >"


MISSING = _Missing()


def get_attr(t, name, default=MISSING):
    value = t.__dict__.get(name, default)
    if value is not get_attr:
        if hasattr(value, '__get__') and type(value) in {staticmethod, classmethod}:
            return getattr(t, name, get_attr)
        else:
            return value
    return getattr(t, name, get_attr)


def del_attr(t, name):
    old = get_attr(t, name, MISSING)
    if old is not MISSING:
        delattr(t, name)
    return old


def set_attr(t, name, value):
    old = get_attr(t, name)
    if isinstance(t.__dict__, MutableMapping):
        t.__dict__[name] = value
    else:
        setattr(t, name, value)
    return old


class PatchMeta(type):
    __enabled__: bool

    def __prepare__(cls, *args, **kwargs):
        return type.__prepare__(*args, **kwargs)

    def __new__(mcs, name, bases, namespace):
        type_to_patch = namespace.pop('__target__', None)
        if type_to_patch is None:
            return type.__new__(mcs, name, bases, {})

        to_delete = namespace.pop('__to_delete__', set())
        to_update = namespace.pop('__to_update__', set())

        patched_attrs = {
            attr: namespace[attr]
            for attr in to_update

        }
        original_attrs = {
            attr: type_to_patch.__dict__[attr]
            for attr in to_update | to_delete
            if attr in type_to_patch.__dict__
        }
        cls = type.__new__(mcs, name, bases, {})

        cls.__target__ = type_to_patch
        cls.__attrs_to_patch__ = patched_attrs
        cls.__original_attrs__ = original_attrs
        cls.__extra__ = (to_update | to_delete) ^ original_attrs.keys()
        cls.__attrs_to_delete__ = to_delete
        cls.__redefined_on_subclasses__ = {}
        cls.__enabled__ = False
        return cls

    def enable(cls):
        target = cls.__target__
        subclasses = _get_all_subclasses(target)

        for attr in cls.__attrs_to_delete__:
            old_value = del_attr(target, attr)
            if old_value is MISSING:
                continue
            for sub_cls in subclasses:
                if get_attr(sub_cls, attr) is old_value:
                    del_attr(sub_cls, attr)
                    cls.__redefined_on_subclasses__.setdefault(attr, set()).add(sub_cls)

        for attr, new_value in cls.__attrs_to_patch__.items():
            old_value = set_attr(target, attr, new_value)
            if old_value is MISSING:
                continue
            cls.__original_attrs__[attr] = old_value
            for sub_cls in subclasses:
                if get_attr(sub_cls, attr) is old_value:
                    set_attr(sub_cls, attr, new_value)
                    cls.__redefined_on_subclasses__.setdefault(attr, set()).add(sub_cls)

        cls.__enabled__ = True

    def disable(cls):
        target = cls.__target__
        for attr, value in cls.__original_attrs__.items():
            set_attr(target, attr, value)
            for sub_cls in cls.__redefined_on_subclasses__.get(attr, ()):
                set_attr(sub_cls, attr, value)

        for attr in cls.__extra__:
            del_attr(target, attr)

        cls.__enabled__ = False


class Patch(metaclass=PatchMeta):
    ...


class PatchedEnumMeta(Patch):
    __target__ = EnumMeta
    __to_delete__ = {'__getattr__'}
    __to_update__ = {'__new__', '__iter__'}

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

            enum_member._name_ = member_name

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
    __to_delete__ = {'name', 'value'}
    __to_update__ = {'__new__', '__setattr__', '__delattr__'}

    def __new__(cls, value):
        """
        All enum instances are actually created during class construction
        without calling this method; this method is called by the metaclass'
        __call__ (i.e. Color(3) ), and by pickle

        Remove SLOW check of _missing_ returns, so it can return invalid Enum!
        """
        # by-value search for a matching enum member
        # see if it's in the reverse mapping (for hashable values)
        if value.__class__ is cls:
            # moved it here in favor of faster lookups by value
            return value
        try:
            return cls._value2member_map_[value]
        except KeyError:
            pass
        except TypeError:
            # not there, now do long search -- O(n) behavior
            for member in cls._member_map_.values():
                if member._value_ == value:
                    return member

        # set member name and value
        possible_member = cls._missing_(value)
        if possible_member is None:
            raise ValueError("%r is not a valid %s" % (value, cls.__name__))
        return possible_member

    def __setattr__(self, key, value):
        if key in {'name', 'value'}:
            raise AttributeError("Can't set attribute")
        elif key in {'_name_', '_value_'}:
            # hook to also set 'value' and 'name' attr
            object.__setattr__(self, key[1:-1], value)
        object.__setattr__(self, key, value)

    def __delattr__(self, key):
        if key in {'name', 'value'}:
            raise AttributeError("Can't del attribute")
        object.__delattr__(self, key)


# faster _decompose version from python 3.9
def _decompose(flag, value):
    """Extract all members from the value."""
    # _decompose is only called if the value is not named
    not_covered = value
    negative = value < 0
    members = []
    for member in flag:
        member_value = member._value_
        if member_value and member_value & value == member_value:
            members.append(member)
            not_covered &= ~member_value
    if not negative:
        tmp = not_covered
        while tmp:
            flag_value = 2 ** _high_bit(tmp)
            if flag_value in flag._value2member_map_:
                members.append(flag._value2member_map_[flag_value])
                not_covered &= ~flag_value
            tmp &= ~flag_value
    if not members and value in flag._value2member_map_:
        members.append(flag._value2member_map_[value])
    members.sort(key=lambda m: m._value_, reverse=True)
    if len(members) > 1 and members[0].value == value:
        # we have the breakdown, don't need the value member itself
        members.pop(0)
    return members, not_covered


def _enable():
    """
    Patches enum for best performance

    :param reload_modules: whether to reload modules after patch or not
    :param exclude_modules: set of modules which will not be reloaded
    :param frame_to_check: frame globals of which will be checked for imported enums (set 0 to skip check)
    """
    patch: PatchMeta
    for patch in Patch.__subclasses__():
        patch.enable()

    # setting missing attributes to enum types and members that were created before patch
    for enum_cls in _get_all_subclasses(Enum):
        unique_members = set(enum_cls._member_names_)
        type.__setattr__(
            enum_cls,
            '_unique_members_',
            {k: v for k, v in enum_cls._member_map_.items() if k in unique_members}
        )
        # e._value2member_map_ can have extra members so prefer it,
        # but it also can be empty if values are unhashable
        for member in (enum_cls._value2member_map_ or enum_cls._member_map_).values():
            object.__setattr__(member, 'name', member._name_)
            object.__setattr__(member, 'value', member._value_)


def _disable():
    """
    Opposite of enable()
    """
    patch: PatchMeta
    for patch in Patch.__subclasses__():
        patch.disable()
