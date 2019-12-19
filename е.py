import fastenum

assert fastenum.enabled

from enum import Enum
assert Enum is fastenum.Enum
assert Enum.__is_fast__()
