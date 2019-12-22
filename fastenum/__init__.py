import enum

from .parcher import _get_all_subclasses, Patch, PatchMeta
from .patches import EnumMetaPatch, EnumPatch, DynamicClassAttributePatch, EnumDictPatch

__all__ = (
    'disable',
    'enable',
    'enabled',
)

enabled = False

orig_decompose = enum._decompose


def enable():
    """
    Patches enum for best performance
    """
    global enabled
    if enabled:
        raise RuntimeError('Nothing to enable: patch is already applied')

    patch: PatchMeta
    for patch in Patch.__subclasses__():
        patch.enable()
    enum._decompose = patches._decompose
    enabled = True


def disable():
    """
    Restores enum to its origin state
    """
    global enabled
    if not enabled:
        raise RuntimeError('Nothing to disable: patch was not applied')

    patch: PatchMeta
    for patch in Patch.__subclasses__():
        patch.disable()
    enum._decompose = orig_decompose
    enabled = False


enable()
