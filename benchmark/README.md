```python
ATTR_ACCESS:
Testing with 1000000 repeats:

    >>> BuiltinEnum.FOO  # 0.339034597 seconds
    <BuiltinEnum.FOO: 'FOO'>

    >>> BuiltinEnum.FOO.value  # 0.9988253439999999 seconds
    'FOO'

Testing with 1000000 repeats:

    >>> PatchedEnum.FOO  # 0.06925175300000008 seconds
    <PatchedEnum.FOO: 'FOO'>

    >>> QratorEnum.FOO  # 0.07271770099999997 seconds
    <QratorEnum.FOO: 'FOO'>

    >>> DiscordEnum.FOO  # 0.06592386700000019 seconds
    <DiscordEnum.FOO: 'FOO'>

    >>> PatchedEnum.FOO.value  # 0.06934381299999992 seconds
    'FOO'

    >>> QratorEnum.FOO.value  # 0.06072996999999991 seconds
    'FOO'

    >>> DiscordEnum.FOO.value  # 0.054826239000000054 seconds
    'FOO'


DiscordEnum   :   0.120750 seconds in total,   0.060120 average (Fastest)
BuiltinEnum   :   1.337860 seconds in total,   0.581925 average, slower than DiscordEnum by x  9.679462 (in average)
PatchedEnum   :   0.138596 seconds in total,   0.069298 average, slower than DiscordEnum by x  1.152667 (in average)
QratorEnum    :   0.133448 seconds in total,   0.066454 average, slower than DiscordEnum by x  1.105366 (in average)


INHERITANCE:
Testing with 1000000 repeats:

    >>> issubclass(BuiltinEnum, Enum)  # 0.1846578179999998 seconds
    True

    >>> isinstance(BuiltinEnum.FOO, Enum)  # 0.30081541499999975 seconds
    True

    >>> isinstance(BuiltinEnum.FOO, BuiltinEnum)  # 0.23010569400000014 seconds
    True

    >>> isinstance(BuiltinEnum.FOO, str)  # 0.2460515889999999 seconds
    True

Testing with 1000000 repeats:

    >>> issubclass(PatchedEnum, Enum)  # 0.1541273440000004 seconds
    True

    >>> issubclass(QratorEnum, Enum)  # 0.17432254900000022 seconds
    False

    >>> issubclass(DiscordEnum, Enum)  # 0.15594098200000017 seconds
    False

    >>> isinstance(PatchedEnum.FOO, Enum)  # 0.23045377 seconds
    True

    >>> isinstance(QratorEnum.FOO, Enum)  # 0.24137184099999986 seconds
    False

    >>> isinstance(DiscordEnum.FOO, Enum)  # 0.20914493700000003 seconds
    False

    >>> isinstance(PatchedEnum.FOO, PatchedEnum)  # 0.10320675700000059 seconds
    True

    >>> isinstance(QratorEnum.FOO, QratorEnum)  # 0.10040993600000014 seconds
    True

    >>> isinstance(DiscordEnum.FOO, DiscordEnum)  # 0.34633623700000005 seconds
    True

    >>> isinstance(PatchedEnum.FOO, str)  # 0.11627604399999925 seconds
    True

    >>> isinstance(QratorEnum.FOO, str)  # 0.12633884900000059 seconds
    True

    >>> isinstance(DiscordEnum.FOO, str)  # 0.15043016200000014 seconds
    False


PatchedEnum   :   0.604064 seconds in total,   0.143686 average (Fastest)
BuiltinEnum   :   0.961631 seconds in total,   0.236813 average, slower than PatchedEnum by x  1.648124 (in average)
QratorEnum    :   0.642443 seconds in total,   0.151998 average, slower than PatchedEnum by x  1.057847 (in average)
DiscordEnum   :   0.861852 seconds in total,   0.203030 average, slower than PatchedEnum by x  1.413008 (in average)


TRYING_VALUES:
Testing with 1000000 repeats:

    >>> try:     BuiltinEnum.FOO = 'new' except: pass  # 0.9492342350000005 seconds
    AttributeError('Cannot reassign members.')

    >>> try:     BuiltinEnum('unknown') except: pass  # 5.5065217849999994 seconds
    ValueError("'unknown' is not a valid BuiltinEnum")

    >>> BuiltinEnum('FOO')  # 0.7844771290000025 seconds
    <BuiltinEnum.FOO: 'FOO'>

    >>> BuiltinEnum(BuiltinEnum.FOO)  # 0.733109000999999 seconds
    <BuiltinEnum.FOO: 'FOO'>

    >>> BuiltinEnum['FOO']  # 0.3065877790000009 seconds
    <BuiltinEnum.FOO: 'FOO'>

Testing with 1000000 repeats:

    >>> try:     PatchedEnum.FOO = 'new' except: pass  # 0.7640039160000001 seconds
    AttributeError('Cannot reassign members.')

    >>> try:     QratorEnum.FOO = 'new' except: pass  # 0.7405447570000021 seconds
    TypeError('Enum-like classes strictly prohibit changing any attribute/property after they are once set')

    >>> try:     DiscordEnum.FOO = 'new' except: pass  # 0.4569283679999998 seconds
    TypeError('Enums are immutable.')

    >>> try:     PatchedEnum('unknown') except: pass  # 1.9096569710000004 seconds
    ValueError("'unknown' is not a valid PatchedEnum")

    >>> try:     QratorEnum('unknown') except: pass  # 0.8517799580000016 seconds
    ValueError('Value unknown is not found in this enum type declaration')

    >>> try:     DiscordEnum('unknown') except: pass  # 1.1884922160000002 seconds
    ValueError("'unknown' is not a valid DiscordEnum")

    >>> PatchedEnum('FOO')  # 0.4758100359999986 seconds
    <PatchedEnum.FOO: 'FOO'>

    >>> QratorEnum('FOO')  # 0.39784907800000013 seconds
    <QratorEnum.FOO: 'FOO'>

    >>> DiscordEnum('FOO')  # 0.2402779069999994 seconds
    <DiscordEnum.FOO: 'FOO'>

    >>> PatchedEnum(PatchedEnum.FOO)  # 0.5433184440000005 seconds
    <PatchedEnum.FOO: 'FOO'>

    >>> QratorEnum(QratorEnum.FOO)  # 1.1917125610000028 seconds
    <QratorEnum.FOO: 'FOO'>

    >>> try:     DiscordEnum(DiscordEnum.FOO) except: pass  # 1.8536693709999987 seconds
    ValueError("<DiscordEnum.FOO: 'FOO'> is not a valid DiscordEnum")

    >>> PatchedEnum['FOO']  # 0.18254251400000143 seconds
    <PatchedEnum.FOO: 'FOO'>

    >>> QratorEnum['FOO']  # 0.2101041059999993 seconds
    <QratorEnum.FOO: 'FOO'>

    >>> DiscordEnum['FOO']  # 0.18098364900000163 seconds
    <DiscordEnum.FOO: 'FOO'>


QratorEnum    :   3.391990 seconds in total,   0.574964 average (Fastest)
BuiltinEnum   :   8.279930 seconds in total,   0.983809 average, slower than QratorEnum by x  1.711080 (in average)
PatchedEnum   :   3.875332 seconds in total,   0.585572 average, slower than QratorEnum by x  1.018451 (in average)
DiscordEnum   :   3.920352 seconds in total,   0.534867 average, slower than QratorEnum by x  0.930262 (in average)


MISC:
Testing with 1000000 repeats:

    >>> sys.getsizeof(BuiltinEnum)  # 0.3024344879999994 seconds
    1064

    >>> sys.getsizeof(BuiltinEnum.FOO)  # 0.42169187800000074 seconds
    100

    >>> for member in BuiltinEnum: pass  # 1.1020697800000008 seconds
    

    >>> dir(BuiltinEnum)  # 0.7576597479999982 seconds
    ['BAR', 'FOO', '__class__', '__doc__', '__members__', '__module__']

    >>> repr(BuiltinEnum)  # 0.6420236060000022 seconds
    "<enum 'BuiltinEnum'>"

Testing with 1000000 repeats:

    >>> sys.getsizeof(PatchedEnum)  # 0.28691167299999876 seconds
    1064

    >>> sys.getsizeof(QratorEnum)  # 0.28854570699999726 seconds
    896

    >>> sys.getsizeof(DiscordEnum)  # 0.28451946799999916 seconds
    1064

    >>> sys.getsizeof(PatchedEnum.FOO)  # 0.2607541659999981 seconds
    100

    >>> sys.getsizeof(QratorEnum.FOO)  # 0.2656812199999976 seconds
    100

    >>> sys.getsizeof(DiscordEnum.FOO)  # 0.2842819829999996 seconds
    56

    >>> for member in PatchedEnum: pass  # 0.3214790119999975 seconds
    

    >>> for member in QratorEnum: pass  # 0.33148565999999846 seconds
    

    >>> for member in DiscordEnum: pass  # 0.7288776139999982 seconds
    

    >>> dir(PatchedEnum)  # 0.5787732339999963 seconds
    ['BAR', 'FOO', '__class__', '__doc__', '__members__', '__module__']

    >>> dir(QratorEnum)  # 24.630986686999996 seconds
    ['BAR', 'FOO', '__add__', '__annotations__', '__call__', '__class__', '__contains__', '__copy__', '__deepcopy__', '__delattr__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getitem__', '__getnewargs__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__iter__', '__le__', '__len__', '__lt__', '__mod__', '__module__', '__mul__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__rmod__', '__rmul__', '__setattr__', '__sizeof__', '__slots__', '__str__', '__subclasshook__', '_base_typed', 'capitalize', 'casefold', 'center', 'count', 'encode', 'endswith', 'expandtabs', 'find', 'format', 'format_map', 'index', 'isalnum', 'isalpha', 'isascii', 'isdecimal', 'isdigit', 'isidentifier', 'islower', 'isnumeric', 'isprintable', 'isspace', 'istitle', 'isupper', 'join', 'ljust', 'lower', 'lstrip', 'maketrans', 'name', 'partition', 'replace', 'rfind', 'rindex', 'rjust', 'rpartition', 'rsplit', 'rstrip', 'split', 'splitlines', 'startswith', 'strip', 'swapcase', 'title', 'translate', 'upper', 'value', 'zfill']

    >>> dir(DiscordEnum)  # 17.887501173000004 seconds
    ['BAR', 'FOO', '__add__', '__class__', '__contains__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getitem__', '__getnewargs__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__iter__', '__le__', '__len__', '__lt__', '__mod__', '__module__', '__mul__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__rmod__', '__rmul__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_enum_member_map_', '_enum_member_names_', '_enum_value_map_', 'capitalize', 'casefold', 'center', 'count', 'encode', 'endswith', 'expandtabs', 'find', 'format', 'format_map', 'index', 'isalnum', 'isalpha', 'isascii', 'isdecimal', 'isdigit', 'isidentifier', 'islower', 'isnumeric', 'isprintable', 'isspace', 'istitle', 'isupper', 'join', 'ljust', 'lower', 'lstrip', 'maketrans', 'partition', 'replace', 'rfind', 'rindex', 'rjust', 'rpartition', 'rsplit', 'rstrip', 'split', 'splitlines', 'startswith', 'strip', 'swapcase', 'title', 'translate', 'try_value', 'upper', 'zfill']

    >>> repr(PatchedEnum)  # 0.5370067930000033 seconds
    "<enum 'PatchedEnum'>"

    >>> repr(QratorEnum)  # 0.29461049399999695 seconds
    "<class '__main__.QratorEnum'>"

    >>> repr(DiscordEnum)  # 0.4948041620000083 seconds
    "<enum 'DiscordEnum'>"


PatchedEnum   :   1.984925 seconds in total,   0.375599 average (Fastest)
BuiltinEnum   :   3.225880 seconds in total,   0.584753 average, slower than PatchedEnum by x  1.556855 (in average)
QratorEnum    :  25.811310 seconds in total,   0.713106 average, slower than PatchedEnum by x  1.898585 (in average)
DiscordEnum   :  19.679984 seconds in total,   0.878011 average, slower than PatchedEnum by x  2.337630 (in average)


TOTAL TIME:

PatchedEnum   :   6.602916 seconds in total,   0.274735 average (Fastest)
BuiltinEnum   :  13.805300 seconds in total,   0.548496 average, slower than PatchedEnum by x  1.996453 (in average)
QratorEnum    :  29.979191 seconds in total,   0.336723 average, slower than PatchedEnum by x  1.225629 (in average)
DiscordEnum   :  24.582938 seconds in total,   0.372982 average, slower than PatchedEnum by x  1.357605 (in average)
```