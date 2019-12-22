from .fastenum import _disable, _enable, PatchedEnum, PatchedEnumMeta

__all__ = (
    'disable',
    'enable',
    'enabled',
)

enabled = False


def enable():
    global enabled
    if enabled:
        raise RuntimeError('Builtin enum is already patched')
    _enable()
    enabled = True


def disable():
    global enabled
    if not enabled:
        raise RuntimeError('Builtin enum was not patched yet')
    _disable()
    enabled = False


enable()
