# fastenum

###### Based on [python/cpython#17669](https://github.com/python/cpython/pull/17669) and [python/cpython#16483](https://github.com/python/cpython/pull/16483)

Patch for stdlib `enum` that makes it *fast*.

## How fast?

- ~10x faster `name`/`value` access
- ~6x faster access to enum members
- ~2x faster values positive check
- ~3x faster values negative check
- ~3x faster iteration
- ~100x faster new `Flags` and `IntFlags` creation for Python 3.8 and below

## Wow this is fast! How do I use it?

First, install it from PyPi using pip

```shell
pip install f-enum
```

or using poetry

```shell
poetry add f-enum
```

Then enable the patch just by calling `fastenum.enable()` once at the start of your programm:

```python
import fastenum

fastenum.enable()
```

You don't need to re-apply patch across different modules: once it's enabled, it'll work everywhere.

## What's changed?

fastenum is designed to give effortless boost for all enums from stdlib. That means that none of optimizations should break existing code, thus requiring no changes other than installing and activating the library.

Here are summary of internal changes:

- Optimized `Enum.__new__`
- Remove `EnumMeta.__getattr__`
- Store `Enum.name` and `.value` in members `__dict__` for faster access
- Replace `Enum._member_names_` with `._unique_member_map_` for faster lookups and iteration (old arg still remains)
- Replace `_EmumMeta._member_names` and `._last_values` with `.members` mapping (old args still remain)
- Add support for direct setting and getting class attrs on `DynamicClassAttribute` without need to use slow `__getattr__`
- Various minor improvements
