import enum
from enum import ( # type: ignore
    Enum,
    EnumMeta,
    _EnumDict,
    auto,
    _auto_null,
    _high_bit,
    _is_descriptor,
    _is_dunder,
    _is_sunder,
    _make_class_unpicklable,
)
from types import DynamicClassAttribute

from fastenum.parcher import Patch, InstancePatch


class DynamicClassAttributePatch(
    Patch, target=DynamicClassAttribute, update={'__init__', '__get__', '__set_name__', 'set_class_attr'}
):
    def __init__(self, fget=None, fset=None, fdel=None, doc=None, alias=None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel

        # next two lines make DynamicClassAttribute act the same as property
        self.__doc__ = doc or fget.__doc__
        self.overwrite_doc = doc is None
        # support for abstract methods
        self.__isabstractmethod__ = bool(getattr(fget, '__isabstractmethod__', False))
        # define name for class attributes
        self.alias = alias

    def __get__(self, instance, ownerclass):
        if instance is None:
            if self.__isabstractmethod__:
                return self
            return getattr(ownerclass, self.alias)
        elif self.fget is None:
            raise AttributeError("unreadable attribute")
        return self.fget(instance)

    def __set_name__(self, ownerclass, alias):
        if self.alias is None:
            self.alias = f'_cls_attr_{alias}'

    def set_class_attr(self, cls, value):
        setattr(cls, self.alias, value)

    @classmethod
    def __run_on_instance__(cls, instance):
        instance.alias = f'_cls_attr_{instance.fget.__name__}'


class EnumPatch(
    Patch,
    target=Enum,
    delete={'name', 'value'},
    update={'__new__', '__setattr__', '__delattr__', '__dir__'},
):
    def __new__(cls, value):
        # all enum instances are actually created during class construction
        # without calling this method; this method is called by the metaclass'
        # __call__ (i.e. Color(3) ), and by pickle

        # using .__class__ instead of type() as it 2x faster
        if value.__class__ is cls:
            # For lookups like Color(Color.RED)
            return value
        # by-value search for a matching enum member
        # see if it's in the reverse mapping (for hashable values)
        try:
            return cls._value2member_map_[value]
        except KeyError:
            # Not found, no need to do long O(n) search
            pass
        except TypeError:
            # not there, now do long search -- O(n) behavior
            for member in cls._unique_member_map_.values():
                if member.value == value:
                    return member
        # still not found -- try _missing_ hook

        # TODO: Maybe remove try/except block and setting __context__ in this case?
        try:
            result = cls._missing_(value)
        except Exception as e:
            if cls._missing_ is Enum._missing_:
                # assuming Enum._missing_ is always raises exception
                # This gives huge boost for standard enum
                raise
            else:
                e.__context__ = ValueError("%r is not a valid %s" % (value, cls.__qualname__))
                raise

        if isinstance(result, cls):
            return result

        ve_exc = ValueError("%r is not a valid %s" % (value, cls.__qualname__))
        if result is None:
            try:
                raise ve_exc
            finally:
                ve_exc = None
        else:
            exc = TypeError(
                'error in %s._missing_: returned %r instead of None or a valid member'
                % (cls.__name__, result)
            )
            exc.__context__ = ve_exc
            try:
                raise exc
            finally:
                exc = None

    def __dir__(self):
        added_behavior = [
            m
            for cls in self.__class__.mro()
            for m in cls.__dict__
            if m[0] != '_' and m not in self._member_map_
        ] + [m for m in self.__dict__ if m[0] != '_']
        return ['__class__', '__doc__', '__module__', 'name', 'value'] + added_behavior

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

    @classmethod
    def __run_on_class__(cls, enum_cls: EnumMeta):  # type: ignore
        cls._set_names(enum_cls)
        cls._set_dynamic_class_attrs(enum_cls)

    @classmethod
    def __run_on_instance__(cls, member: Enum):  # type: ignore
        member.__dict__['name'] = member._name_
        member.__dict__['value'] = member._value_

    @classmethod
    def _set_names(cls, enum_cls):
        unique_members = set(enum_cls._member_names_)
        type.__setattr__(
            enum_cls,
            '_unique_member_map_',
            {k: v for k, v in enum_cls._member_map_.items() if k in unique_members}
        )

    @classmethod
    def _set_dynamic_class_attrs(cls, enum_cls):
        assert DynamicClassAttributePatch.__enabled__, 'DynamicClassAttr must be patched first'
        assert not EnumMetaPatch.__enabled__, 'EnumMetaPatch.__getattr__ method is needed for retrieving class attrs'

        for k, v in enum_cls.__dict__.items():
            if isinstance(v, DynamicClassAttribute):
                try:
                    v.set_class_attr(enum_cls, getattr(enum_cls, k))
                except AttributeError:
                    pass


class EnumDictPatch(
    Patch, target=_EnumDict, update={'__init__', '__setitem__', '_member_names', '_last_values'}
):

    def __init__(self):
        dict.__init__(self)
        self.members = {}
        self._ignore = []
        self._auto_called = False

    def __setitem__(self, key, value):
        """Changes anything not dundered or not a descriptor.

        If an enum member name is used twice, an error is raised; duplicate
        values are not checked for.

        Single underscore (sunder) names are reserved.

        """
        if _is_sunder(key):
            import warnings
            warnings.warn(
                    "private variables, such as %r, will be normal attributes in 3.10"
                        % (key, ),
                    DeprecationWarning,
                    stacklevel=2,
                    )
            if key not in {
                '_order_', '_create_pseudo_member_',
                '_generate_next_value_', '_missing_', '_ignore_',
            }:
                raise ValueError('_names_ are reserved for future Enum use')
            if key == '_generate_next_value_':
                # check if members already defined as auto()
                if self._auto_called:
                    raise TypeError("_generate_next_value_ must be defined before members")
                setattr(self, '_generate_next_value', value)
            elif key == '_ignore_':
                if isinstance(value, str):
                    value = value.replace(',', ' ').split()
                else:
                    value = list(value)
                self._ignore = value
                already = set(value) & self.members.keys()
                if already:
                    raise ValueError('_ignore_ cannot specify already set names: %r' % (already,))
        elif _is_dunder(key):
            if key == '__order__':
                key = '_order_'
        elif key in self.members:
            # descriptor overwriting an enum?
            raise TypeError('Attempted to reuse key: %r' % key)
        elif key in self._ignore:
            pass
        elif not _is_descriptor(value):
            if key in self:
                # enum overwriting a descriptor?
                raise TypeError('%r already defined as: %r' % (key, self[key]))
            if isinstance(value, auto):
                if value.value == _auto_null:
                    value.value = self._generate_next_value(key, 1, len(self.members), list(self.members.values()))
                    self._auto_called = True
                value = value.value
            self.members[key] = value
        dict.__setitem__(self, key, value)

    @property
    def _member_names(self):
        return list(self.members)

    @property
    def _last_values(self):
        return list(self.members.values())


class EnumMetaPatch(
    type, Patch, target=EnumMeta, delete={'__getattr__'}, update={'__new__', '__iter__'}
):

    def __new__(metacls, cls, bases, classdict):
        # an Enum class is final once enumeration items have been defined; it
        # cannot be mixed with other types (int, float, etc.) if it has an
        # inherited __new__ unless a new __new__ is defined (or the resulting
        # class will fail).
        #
        # remove any keys listed in _ignore_
        classdict.setdefault('_ignore_', []).append('_ignore_')
        ignore = classdict['_ignore_']
        for key in ignore:
            classdict.pop(key, None)
        member_type, first_enum = metacls._get_mixins_(cls, bases)
        __new__, save_new, use_args = metacls._find_new_(classdict, member_type,
                                                         first_enum)

        # save enum items into separate mapping so they don't get baked into
        # the new class
        enum_members = classdict.members
        for name in enum_members:
            del classdict[name]

        # adjust the sunders
        _order_ = classdict.pop('_order_', None)

        # check for illegal enum names (any others?)
        invalid_names = enum_members.keys() & {'mro', ''}
        if invalid_names:
            raise ValueError('Invalid enum member name: {0}'.format(
                ','.join(invalid_names)))

        # create a default docstring if one has not been provided
        if '__doc__' not in classdict:
            classdict['__doc__'] = 'An enumeration.'

        # create our new Enum type
        enum_class = type.__new__(metacls, cls, bases, classdict)
        enum_class._member_names_ = []  # names in definition order
        enum_class._member_map_ = {}  # name->value map
        enum_class._unique_member_map_ = {}
        enum_class._member_type_ = member_type

        dynamic_attributes = {k: v for c in enum_class.mro()
                              for k, v in c.__dict__.items()
                              if isinstance(v, DynamicClassAttribute)}

        # Reverse value->name map for hashable values.
        enum_class._value2member_map_ = {}

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
        if '__reduce_ex__' not in classdict:
            if member_type is not object:
                methods = {'__getnewargs_ex__', '__getnewargs__',
                           '__reduce_ex__', '__reduce__'}
                if not any(m in member_type.__dict__ for m in methods):
                    if '__new__' in classdict:
                        # too late, sabotage
                        _make_class_unpicklable(enum_class)
                    else:
                        # final attempt to verify that pickling would work:
                        # travel mro until __new__ is found, checking for
                        # __reduce__ and friends along the way -- if any of them
                        # are found before/when __new__ is found, pickling should
                        # work
                        sabotage = None
                        for chain in bases:
                            for base in chain.__mro__:
                                if base is object:
                                    continue
                                elif any(m in base.__dict__ for m in methods):
                                    # found one, we're good
                                    sabotage = False
                                    break
                                elif '__new__' in base.__dict__:
                                    # not good
                                    sabotage = True
                                    break
                            if sabotage is not None:
                                break
                        if sabotage:
                            _make_class_unpicklable(enum_class)

        # instantiate them, checking for duplicates as we go
        # we instantiate first instead of checking for duplicates first in case
        # a custom __new__ is doing something funky with the values -- such as
        # auto-numbering ;)
        for member_name, value in enum_members.items():
            if not isinstance(value, tuple):
                args = (value,)
            else:
                args = value
            if member_type is tuple:  # special case for tuple enums
                args = (args,)  # wrap it one more time
            if not use_args:
                enum_member = __new__(enum_class)
                if not hasattr(enum_member, 'value'):
                    enum_member._value_ = value
            else:
                enum_member = __new__(enum_class, *args)
                if not hasattr(enum_member, 'value'):
                    if member_type is object:
                        enum_member._value_ = value
                    else:
                        enum_member._value_ = member_type(*args)

            value = enum_member.value
            enum_member._name_ = member_name
            # setting protected attributes
            enum_member.__objclass__ = enum_class
            enum_member.__init__(*args)
            # If another member with the same value was already defined, the
            # new member becomes an alias to the existing one.
            for name, canonical_member in enum_class._member_map_.items():
                if canonical_member.value == enum_member.value:
                    enum_member = canonical_member
                    break
            else:
                # Aliases don't appear in member names (only in __members__).
                enum_class._unique_member_map_[member_name] = enum_member
                enum_class._member_names_.append(member_name)

            dynamic_attr: DynamicClassAttributePatch = dynamic_attributes.get(member_name)
            if dynamic_attr is not None:
                # Setting attrs respectively to dynamic attribute so access member_name
                # through a class will be routed to enum_member
                # setattr(enum_class, dynamic_attr.class_attr_name, enum_member)
                # name and value dynamic attrs are deleted from EnumMeta and shouldn't fall in this condition at this point
                # this is just a way to support any user defined dynamic class attrs
                dynamic_attr.set_class_attr(enum_class, enum_member)
            else:
                setattr(enum_class, member_name, enum_member)

            # now add to _member_map_
            enum_class._member_map_[member_name] = enum_member
            try:
                # This may fail if value is not hashable. We can't add the value
                # to the map, and by-value lookups for this value will be
                # linear.
                enum_class._value2member_map_[value] = enum_member
            except TypeError:
                pass

        # double check that repr and friends are not the mixin's or various
        # things break (such as pickle)
        for name in ('__repr__', '__str__', '__format__', '__reduce_ex__'):
            if name in classdict:
                continue
            class_method = getattr(enum_class, name)
            obj_method = getattr(member_type, name, None)
            enum_method = getattr(first_enum, name, None)
            if obj_method is not None and obj_method is class_method:
                setattr(enum_class, name, enum_method)

        # replace any other __new__ with our own (as long as Enum is not None,
        # anyway) -- again, this is to support pickle
        if Enum is not None:
            # if the user defined their own __new__, save it before it gets
            # clobbered in case they subclass later
            if save_new:
                enum_class.__new_member__ = __new__
            enum_class.__new__ = Enum.__new__

        # py3 support for definition order (helps keep py2/py3 code in sync)
        if _order_ is not None:
            if isinstance(_order_, str):
                _order_ = _order_.replace(',', ' ').split()
            if _order_ != list(enum_class._unique_member_map_):
                raise TypeError('member order does not match _order_')

        return enum_class

    def __iter__(cls):
        return iter(cls._unique_member_map_.values())

    def __reversed__(cls):
        return reversed(list(cls._unique_member_map_.values()))


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


InstancePatch.new(target=enum, update={'_decompose': _decompose})
