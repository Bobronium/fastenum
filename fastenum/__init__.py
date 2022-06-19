from fastenum import patches  # just to execute module
from fastenum.parcher import Patch, InstancePatch

assert patches, "Need to load this module"

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
        raise RuntimeError('Nothing to disable: patch was not applied previously')

    Patch.disable_patches()
    InstancePatch.disable_patches()
    enabled = False
