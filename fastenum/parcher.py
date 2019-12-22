import gc
from typing import MutableMapping, Any, Set, Type, Callable


class _Missing:
    def __repr__(self):
        return "< 'MISSING' >"


MISSING = _Missing()


def _get_all_subclasses(cls):
    all_subclasses = set()
    for subclass in type.__subclasses__(cls):
        all_subclasses.add(subclass)
        all_subclasses.update(_get_all_subclasses(subclass))

    return all_subclasses


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

    __run_on_class__: Callable[[Type[Any]], None]
    __run_on_instance__: Callable[[Any], None]

    def __prepare__(cls, *args, **kwargs):
        return type.__prepare__(*args, **kwargs)

    def __new__(mcs, name, bases, namespace, target=None, delete=None, update=None, keep=None):
        target = target or namespace.pop('__target__', None)
        if target is None:
            return type.__new__(mcs, name, bases, namespace)

        to_delete = delete or namespace.pop('__to_delete__', set())
        to_update = update or namespace.pop('__to_update__', set())
        to_keep = keep or namespace.pop('__to_keep__', set())

        patched_attrs = {
            attr: namespace[attr]
            for attr in to_update

        }
        original_attrs = {
            attr: target.__dict__[attr]
            for attr in to_update | to_delete
            if attr in target.__dict__
        }
        cls = type.__new__(mcs, name, bases, namespace)

        cls.__target__ = target
        cls.__to_update__ = patched_attrs
        cls.__original_attrs__ = original_attrs
        cls.__extra__ = (to_update | to_delete) ^ (original_attrs.keys() | to_keep)
        cls.__to_delete__ = to_delete
        cls.__redefined_on_subclasses__ = {}
        cls.__enabled__ = False
        return cls

    def enable(cls):
        target = cls.__target__
        subclasses = _get_all_subclasses(target)

        if cls.__run_on_class__:
            cls.__run_on_class__(target)
            for sub_cls in subclasses:
                cls.__run_on_class__(sub_cls)

        if cls.__run_on_instance__:
            for obj in gc.get_objects():
                if isinstance(obj, target):
                    cls.__run_on_instance__(obj)

        for attr in cls.__to_delete__:
            old_value = del_attr(target, attr)
            if old_value is MISSING:
                continue
            for sub_cls in subclasses:
                if get_attr(sub_cls, attr) is old_value:
                    del_attr(sub_cls, attr)
                    cls.__redefined_on_subclasses__.setdefault(attr, set()).add(sub_cls)

        for attr, new_value in cls.__to_update__.items():
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
    """Class to declare attributes to patch other classes"""

    __target__: Type[Any]
    __to_update__: Set[str]
    __to_delete__: Set[str]
    __enabled__: bool

    __run_on_class__: Callable[[Type[Any]], None] = None
    __run_on_instance__: Callable[[Any], None] = None
