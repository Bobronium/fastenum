# fastenum
#### Patch for builtin `enum` module to achieve best performance

This patch is based on
[python/cpython#17669](https://github.com/python/cpython/pull/17669) and [python/cpython#16483](https://github.com/python/cpython/pull/16483) 

### Why?
- ~100x faster new `Flags` and `IntFlags` creation
- ~10x faster `name`/`value` access
- ~6x faster access to enum members
- ~2x faster values positive check
- ~3x faster values negative check
- ~3x faster iteration


### Wow it's fast! How I do use it?
To enable patch, just import fastenum once:
```python
import fastenum

assert fastenum.enabled
```
After you imported fastenum package, all your Enums are patched and fast!

You don't need to re-apply patch across different modules: once it's patched it'll work everywhere.


### What's changed?
All changes are backwards compatible, so you should be ok with any of your existing code. 
But of course, always test first!
- Optimized `Enum.__new__`
- Remove `EnumMeta.__getattr__`
- Store `Enum.name` and `.value` in members `__dict__` for faster access
- Replace `Enum._member_names_` with `._unique_member_map_` for faster lookups and iteration (old arg still remains)
- Replace `_EmumMeta._member_names` and `._last_values` with `.members` mapping (old args still remain)
- Add support for direct setting and getting class attrs on `DynamicClassAttribute` without need to use slow `__getattr__`
- Various minor improvements
