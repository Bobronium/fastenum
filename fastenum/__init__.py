"""Patch for builtin enum module to achieve best performance"""

from .fastenum import enable, disable, enabled
