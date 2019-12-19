"""Patch for builtin enum module to achieve best performance"""

from .fastenum import (
    EnumMeta,
    Enum,
    IntEnum,
    Flag,
    IntFlag,
    auto,
    unique,
    BuiltinEnumMeta,
    BuiltinEnum,
    BuiltinIntEnum,
    BuiltinFlag,
    BuiltinIntFlag,
    enable,
    disable,
    enabled,
    enum,
)

__all__ = [
    'EnumMeta',
    'Enum', 'IntEnum', 'Flag', 'IntFlag',
    'BuiltinEnumMeta',
    'BuiltinEnum', 'BuiltinIntEnum', 'BuiltinFlag', 'BuiltinIntFlag',
    'auto', 'unique', 'enable', 'disable',
    'enum'
]
