from enum import Enum

from .parcher import _get_all_subclasses, Patch, PatchMeta
from .patches import EnumMetaPatch, EnumPatch

__all__ = (
    'disable',
    'enable',
    'enabled',
)

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
    enabled = True


def disable():
    """
    Opposite of enable()
    """
    global enabled
    if not enabled:
        raise RuntimeError('Builtin enum was not patched yet')

    patch: PatchMeta
    for patch in Patch.__subclasses__():
        patch.disable()
    enabled = False


enable()
