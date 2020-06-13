from . import patches  # just to execute module
from .parcher import Patch, PatchMeta, InstancePatch

__all__ = (
    'disable',
    'enable',
    'enabled',
)

enabled: bool = False


def enable() -> None:
    """
    Patches enum for best performance
    """
    global enabled
    if enabled:
        raise RuntimeError('Nothing to enable: patch is already applied')

    Patch.enable_patches()
    InstancePatch.enable_patches()
    enabled = True


def disable() -> None:
    """
    Restores enum to its origin state
    """
    global enabled
    if not enabled:
        raise RuntimeError('Nothing to disable: patch was not applied')

    Patch.disable_patches()
    InstancePatch.disable_patches()
    enabled = False


enable()
