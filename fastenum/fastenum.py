import enum
import os
import sys
from enum import (
    EnumMeta as BuiltinEnumMeta,
    Enum as BuiltinEnum,
    IntEnum as BuiltinIntEnum,
    Flag as BuiltinFlag,
    IntFlag as BuiltinIntFlag,
    auto,
    unique,
    _make_class_unpicklable,
    _decompose,
    _high_bit,
)

__all__ = [
    'EnumMeta',
    'Enum', 'IntEnum', 'Flag', 'IntFlag',
    'BuiltinEnumMeta',
    'BuiltinEnum', 'BuiltinIntEnum', 'BuiltinFlag', 'BuiltinIntFlag',
    'auto', 'unique', 'enable', 'disable', 'enabled'
]

if os.environ.get('DISABLE_FASTENUM_AUTO_PATCH'):
    AUTO_PATCH = False
else:
    AUTO_PATCH = True


def _get_all_subclasses(cls):
    all_subclasses = {cls.__name__: cls}
    for subclass in cls.__subclasses__():
        all_subclasses[subclass.__name__] = subclass
        all_subclasses.update(_get_all_subclasses(subclass))

    return all_subclasses


BUILTIN_ENUMS = _get_all_subclasses(BuiltinEnum)

enabled = False

# need to delete these as they really slowing things down
_enums_getattr = BuiltinEnumMeta.__getattr__
_enums_name = BuiltinEnum.__dict__['name']
_enums_value = BuiltinEnum.__dict__['value']


def _reload_modules(exclude: set):
    import importlib

    exclude = exclude | {__name__, '__main__', 'enum', 'py.test'}
    include = {'sre_paese'}
    enum_mentions = BUILTIN_ENUMS.keys() | {'enum'}
    for name, module in sys.modules.copy().items():
        if name.startswith('_pytest') or name in exclude:
            continue
        if name not in include and not module.__dict__.keys() & enum_mentions:
            continue
        importlib.reload(module)


def enable(reload_modules: bool = True, exclude_modules: set = None, frame_to_check: int = 1):
    """
    Patches enum for best performance

    :param reload_modules: whether to reload modules after patch or not
    :param exclude_modules: set of modules which will not be reloaded
    :param frame_to_check: frame globals of which will be checked for imported enums (set 0 to skip check)
    """
    global enabled
    if enabled:
        raise RuntimeError('Builtin enum is already patched')

    inspect = reload_inspect = None
    if frame_to_check:
        reload_inspect = 'inspect' in sys.modules
        import inspect
        current = inspect.currentframe()
        outer = inspect.getouterframes(current)
        outer_locals = outer[frame_to_check].frame.f_locals.keys()

        imported_enums = outer_locals & BUILTIN_ENUMS.keys()
        if imported_enums:
            raise RuntimeError(f'Use it before importing built-in enums: {imported_enums}')

    del BuiltinEnum.name
    del BuiltinEnum.value
    del BuiltinEnumMeta.__getattr__

    # setting name and value for all created enums,
    # just in case they already was used and we couldn't
    # track them, otherwise getting name or value attrs
    # will raise AttributeError on them
    for e in BUILTIN_ENUMS.values():
        for m in e:
            object.__setattr__(m, 'name', m._name_)
            object.__setattr__(m, 'value', m._value_)

    enum.EnumMeta = EnumMeta
    enum.Enum = Enum
    enum.IntEnum = IntEnum
    enum.IntFlag = IntFlag
    enum.Flag = Flag

    enabled = True

    exclude = exclude_modules or set()
    if reload_modules:
        _reload_modules(exclude)
    elif reload_inspect and 'inspect' not in exclude:
        import importlib
        importlib.reload(inspect)


def disable(reload_modules=True, exclude_modules: set = None):
    """
    Opposite of enable()
    """
    global enabled

    if not enabled:
        raise RuntimeError('Builtin enum was not patched')

    BuiltinEnum.name = _enums_name
    BuiltinEnum.value = _enums_value
    BuiltinEnumMeta.__getattr__ = _enums_getattr

    enum.EnumMeta = BuiltinEnumMeta
    enum.Enum = BuiltinEnum
    enum.IntEnum = IntEnum
    enum.IntFlag = BuiltinIntFlag
    enum.Flag = BuiltinFlag

    enabled = False
    if reload_modules:
        _reload_modules(exclude_modules or set())


# Dummy value for Enum as EnumMeta explicitly checks for it, but of course
# until EnumMeta finishes running the first time the Enum class doesn't exist.
# This is also why there are checks in EnumMeta like `if Enum is not None`
Enum = None


class EnumMeta(BuiltinEnumMeta):
    """Metaclass for Enum"""

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
        namespace['__builtin_type__'] = first_enum
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

    def __instancecheck__(cls, instance):
        return isinstance(instance, cls.__builtin_type__)

    def __subclasscheck__(cls, subclass):
        return issubclass(subclass, cls.__builtin_type__)

    def __iter__(cls):
        return iter(cls._unique_members_.values())

    @staticmethod
    def _get_mixins_(bases):
        """Returns the type for creating enum members, and the first inherited
        enum class.

        bases: the tuple of bases that was given to __new__

        """
        if not bases:
            return object, Enum

        def _find_data_type(bases):
            for chain in bases:
                for base in chain.__mro__:
                    if base is object:
                        continue
                    elif '__new__' in base.__dict__:
                        if issubclass(base, BuiltinEnum):
                            continue
                        return base

        # ensure final parent class is an Enum derivative, find any concrete
        # data type, and check that Enum has no members
        first_enum = bases[-1]
        if not issubclass(first_enum, BuiltinEnum):
            raise TypeError("new enumerations should be created as "
                            "`EnumName([mixin_type, ...] [data_type,] enum_type)`")
        member_type = _find_data_type(bases) or object
        if first_enum._member_names_:
            raise TypeError("Cannot extend enumerations")
        return member_type, first_enum


class Enum(BuiltinEnum, metaclass=EnumMeta):
    __builtin_type__: BuiltinEnum

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
        if key in ('name', 'value'):
            raise AttributeError()
        object.__setattr__(self, key, value)

    def __delattr__(self, key):
        if key in ('name', 'value'):
            raise AttributeError()
        object.__delattr__(self, key, value)

    @classmethod
    def __is_fast__(cls):
        return enabled


class IntEnum(Enum, BuiltinIntEnum):
    ...


class Flag(Enum, BuiltinFlag):
    @classmethod
    def _create_pseudo_member_(cls, value):
        possible_member = super()._create_pseudo_member_(value)
        object.__setattr__(possible_member, 'value', possible_member._value_)
        object.__setattr__(possible_member, 'name', possible_member._name_)
        return possible_member


class IntFlag(Flag, BuiltinIntFlag):
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


EnumMeta.__module__ = Enum.__module__ = IntEnum.__module__ = Flag.__module__ = IntFlag.__module__ = 'fastenum'

if AUTO_PATCH and __name__ != '__main__':
    # from enum import Enum  <-- it may fail because of this
    # import fastenum
    #
    # to avoid such behavior:
    #   - use `import enum` instead of `from enum import Enum`
    #   - import enums from `enum` module after patch is complete
    #   - disable auto patch, by setting os.environ['DISABLE_FASTENUM_AUTO_PATCH'] to True

    # frame 7 is the frame of module from which current module is imported
    enable(frame_to_check=7)
