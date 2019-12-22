from enum import EnumMeta, _make_class_unpicklable, Enum, _high_bit

from fastenum.parcher import Patch


class EnumMetaPatch(
    Patch, target=EnumMeta, delete={'__getattr__'}, update={'__new__', '__iter__'}
):
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


class EnumPatch(
    Patch, target=Enum, delete={'name', 'value'}, update={'__new__', '__setattr__', '__delattr__'}
):
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
