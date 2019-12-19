# fastenum
#### Patch for builtin `enum` module to achieve best performance

### TL;DR
- up to 6x faster members access
- up to 10x faster members `name`/`value` access
- up to 2x faster values positive check
- up to 3x faster values negative check
- up to 3x faster iteration


#### To enable fastenum, just import it once:
```python
import fastenum
assert fastenum.enabled

from enum import Enum
assert Enum is fastenum.Enum
assert Enum.__is_fast__()
```
###### **Make sure you import it before importing anything else, otherwise things could (will) break**

For difference in speed see `benchmarks/`


I feel that this actually needs to be in stdlib, but patching all this stuff was actually easier for me that opening issue in python bug tracker
