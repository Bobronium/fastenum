from __future__ import annotations
import gc
from typing import MutableMapping, Any, AbstractSet, Type, Callable, Dict, Tuple, Mapping, Optional, Set, cast


class _Missing:
    def __repr__(self) -> str:
        return "< 'MISSING' >"


MISSING = _Missing()


def get_attr(t: Any, name: str, default: Optional[Any] = MISSING) -> Any:
    value = t.__dict__.get(name, default)
    if value is not get_attr:
        if hasattr(value, '__get__') and type(value) in {staticmethod, classmethod}:
            return getattr(t, name, get_attr)
        else:
            return value
    return getattr(t, name, get_attr)


def del_attr(t: Any, name: str) -> Any:
    old = get_attr(t, name, MISSING)
    if old is not MISSING:
        delattr(t, name)
    return old


def set_attr(t: Any, name: str, value: Any) -> Any:
    old = get_attr(t, name)
    if isinstance(t.__dict__, MutableMapping):
        t.__dict__[name] = value
    else:
        setattr(t, name, value)
    return old


class PatchMeta(type):
    __enabled__: bool
    __run_on_class__: classmethod
    __run_on_instance__: classmethod

    __target__: Type[Any]
    __to_update__: dict[str, Any]
    __to_delete__: AbstractSet[str]
    __original_attrs__: dict[Any, Any]
    __extra__: AbstractSet[str]
    __redefined_on_subclasses__: dict[str, Any]

    def __prepare__(cls, *args: Any, **kwargs: Any) -> Mapping[str, Any]:  # type: ignore
        return type.__prepare__(*args, **kwargs)

    def __new__(
            mcs,
            name: str,
            bases: Tuple[Type[Any], ...],
            namespace: Dict[str, Any],
            target: Any = None,
            delete: AbstractSet[str] = None,
            update: AbstractSet[str] = None
    ) -> PatchMeta:
        target = target or namespace.pop('__target__', None)
        if target is None:
            return type.__new__(mcs, name, bases, namespace)

        to_delete = cast(set, delete or namespace.pop('__to_delete__', set()))
        to_update = cast(set, update or namespace.pop('__to_update__', set()))

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
        cls.__extra__ = (to_update | to_delete) ^ original_attrs.keys()
        cls.__to_delete__ = to_delete
        cls.__redefined_on_subclasses__ = {}
        cls.__enabled__ = False
        return cls

    def enable(cls, check: bool = True) -> None:
        if check and cls.__enabled__:
            raise RuntimeError(f"{cls} is already enabled")

        try:
            target = cls.__target__
        except AttributeError:
            raise TypeError("This patch doesn't have a target. You should define it on its subclass")
        subclasses = cls._get_all_subclasses(target)

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

    def disable(cls, check: bool = True) -> None:
        if check and not cls.__enabled__:
            raise RuntimeError(f"{cls} is already disabled")

        target = cls.__target__
        for attr, value in cls.__original_attrs__.items():
            set_attr(target, attr, value)
            for sub_cls in cls.__redefined_on_subclasses__.get(attr, ()):
                set_attr(sub_cls, attr, value)

        for attr in cls.__extra__:
            del_attr(target, attr)

        cls.__enabled__ = False

    def enable_patches(cls, check: bool = True) -> None:
        """This method is used to apply all defined patches"""
        if hasattr(cls, '__target__'):
            raise TypeError('To apply one particular patch, use .enable() method.')

        for patch in cls.__subclasses__():
            patch.enable(check)

    def disable_patches(cls, check: bool = True) -> None:
        """This method is used to disable all defined patches"""
        if hasattr(cls, '__target__'):
            raise TypeError('To apply one particular patch, use .enable() method.')

        for patch in cls.__subclasses__():
            patch.disable(check)

    def _get_all_subclasses(cls, target: Type[Any]) -> Set[Type[Any]]:
        all_subclasses = set()
        for subclass in type.__subclasses__(target):
            all_subclasses.add(subclass)
            all_subclasses.update(cls._get_all_subclasses(subclass))

        return all_subclasses


class Patch(metaclass=PatchMeta):
    """Class to declare attributes to patch other classes"""
    __enabled__: bool = False

    __run_on_class__: Callable[[Type[Any]], None] | None = None
    __run_on_instance__: Callable[[Any], None] | None = None


class InstancePatchMeta(PatchMeta):
    def _get_all_subclasses(cls, target: Any) -> Set[Type[Any]]:
        return set()

    def new(
            cls, target: Any, delete: AbstractSet[str] = None, update: Dict[str, Any] = None
    ) -> InstancePatchMeta:
        return cast(InstancePatchMeta, cls.__class__.__new__(
            mcs=cls.__class__,
            name=getattr(target, '__name__', target.__class__.__name__) + 'Patch',
            bases=(cls,),
            namespace=update or {},
            target=target,
            delete=delete,
            update=update.keys() if update else None,
        ))


class InstancePatch(metaclass=InstancePatchMeta):
    __run_on_class__ = None
    __run_on_instance__ = None
