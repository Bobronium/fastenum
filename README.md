# fastenum
#### Patch for builtin `enum` module to achieve best performance

### TL;DR
- up to 6x faster members access
- up to 10x faster members `name`/`value` access
- up to 2x faster values positive check
- up to 3x faster values negative check
- up to 3x faster iteration



#### To enable patch, just import fastenum once:
###### **Make sure you import it before importing anything else, otherwise things could (will) break**
```python
import fastenum
assert fastenum.enabled

from enum import Enum
assert Enum.__is_fast__()
```

#### What's changed?
- `EnumMeta.__getattr__` is removed
- `DynamicClassAttribute` is removed in favor of instance attributes
- `name`/`value` are ordinal attributes and put in `__slots__` when possible
- `_missing_` type check is removed, as it was re-e-e-ally slowing things down  _(kinda breaking change, but who cares?)_
- `_order_` was removed as since python 3.6 dicts preserve order
- some other minor improvements

I feel that this actually needs to be in stdlib, but patching all this stuff was actually easier for me that opening issue in python bug tracker
