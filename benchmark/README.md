```python
ATTR_ACCESS:
Testing with 1000000 repeats:

    >>> BuiltinEnum.FOO  # 0.24018136799999998 seconds
    <BuiltinEnum.FOO: 'FOO'>

    >>> BuiltinEnum.FOO.value  # 0.710737864 seconds
    'FOO'

Testing with 1000000 repeats:

    >>> PatchedEnum.FOO  # 0.03859757600000013 seconds
    <PatchedEnum.FOO: 'FOO'>

    >>> QratorEnum.FOO  # 0.039429358000000025 seconds
    <QratorEnum.FOO: FOO>

    >>> DiscordEnum.FOO  # 0.041345793000000075 seconds
    <DiscordEnum.FOO: 'FOO'>

    >>> PatchedEnum.FOO.value  # 0.066078254 seconds
    'FOO'

    >>> QratorEnum.FOO.value  # 0.10349147999999997 seconds
    'FOO'

    >>> DiscordEnum.FOO.value  # 0.1418350439999998 seconds
    'FOO'


PatchedEnum   :   0.104676 seconds in total,   0.050502 average (Fastest)
BuiltinEnum   :   0.950919 seconds in total,   0.413166 average, slower than PatchedEnum by x  8.181164 (in average)
QratorEnum    :   0.142921 seconds in total,   0.063880 average, slower than PatchedEnum by x  1.264890 (in average)
DiscordEnum   :   0.183181 seconds in total,   0.076579 average, slower than PatchedEnum by x  1.516345 (in average)


INHERITANCE:
Testing with 1000000 repeats:

    >>> issubclass(BuiltinEnum, Enum)  # 0.2256329640000001 seconds
    True

    >>> isinstance(BuiltinEnum.FOO, Enum)  # 0.31415773699999994 seconds
    True

    >>> isinstance(BuiltinEnum.FOO, BuiltinEnum)  # 0.2272313589999999 seconds
    True

    >>> isinstance(BuiltinEnum.FOO, str)  # 0.2641942959999999 seconds
    False

Testing with 1000000 repeats:

    >>> issubclass(PatchedEnum, Enum)  # 0.14807156100000007 seconds
    True

    >>> issubclass(QratorEnum, Enum)  # 0.2775659749999999 seconds
    False

    >>> issubclass(DiscordEnum, Enum)  # 0.18641203599999967 seconds
    False

    >>> isinstance(PatchedEnum.FOO, Enum)  # 0.18354563099999988 seconds
    True

    >>> isinstance(QratorEnum.FOO, Enum)  # 0.22613586500000027 seconds
    False

    >>> isinstance(DiscordEnum.FOO, Enum)  # 0.212517053 seconds
    False

    >>> isinstance(PatchedEnum.FOO, PatchedEnum)  # 0.11110581400000008 seconds
    True

    >>> isinstance(QratorEnum.FOO, QratorEnum)  # 0.10475144699999994 seconds
    True

    >>> isinstance(DiscordEnum.FOO, DiscordEnum)  # 0.3129563700000002 seconds
    True

    >>> isinstance(PatchedEnum.FOO, str)  # 0.14141227599999961 seconds
    False

    >>> isinstance(QratorEnum.FOO, str)  # 0.14574088799999974 seconds
    False

    >>> isinstance(DiscordEnum.FOO, str)  # 0.14767039399999948 seconds
    False


PatchedEnum   :   0.584135 seconds in total,   0.143751 average (Fastest)
BuiltinEnum   :   1.031216 seconds in total,   0.255409 average, slower than PatchedEnum by x  1.776747 (in average)
QratorEnum    :   0.754194 seconds in total,   0.175942 average, slower than PatchedEnum by x  1.223938 (in average)
DiscordEnum   :   0.859556 seconds in total,   0.206853 average, slower than PatchedEnum by x  1.438969 (in average)


TRYING_VALUES:
Testing with 1000000 repeats:

    >>> try:     BuiltinEnum.FOO = 'new' except: pass  # 0.8144856690000006 seconds
    AttributeError('Cannot reassign members.')

    >>> try:     BuiltinEnum('unknown') except: pass  # 5.683279208 seconds
    ValueError("'unknown' is not a valid BuiltinEnum")

    >>> BuiltinEnum('FOO')  # 0.7139183350000007 seconds
    <BuiltinEnum.FOO: 'FOO'>

    >>> BuiltinEnum(BuiltinEnum.FOO)  # 0.6875957909999997 seconds
    <BuiltinEnum.FOO: 'FOO'>

    >>> BuiltinEnum['FOO']  # 0.28612421000000055 seconds
    <BuiltinEnum.FOO: 'FOO'>

Testing with 1000000 repeats:

    >>> try:     PatchedEnum.FOO = 'new' except: pass  # 0.6877662439999987 seconds
    AttributeError('Cannot reassign members.')

    >>> try:     QratorEnum.FOO = 'new' except: pass  # 0.7021067549999991 seconds
    TypeError('Enum-like classes strictly prohibit changing any attribute/property after they are once set')

    >>> try:     DiscordEnum.FOO = 'new' except: pass  # 0.41968300599999964 seconds
    TypeError('Enums are immutable.')

    >>> try:     PatchedEnum('unknown') except: pass  # 1.930235720999999 seconds
    ValueError("'unknown' is not a valid PatchedEnum")

    >>> try:     QratorEnum('unknown') except: pass  # 0.7956154479999995 seconds
    ValueError('Value unknown is not found in this enum type declaration')

    >>> try:     DiscordEnum('unknown') except: pass  # 1.1077797060000023 seconds
    ValueError("'unknown' is not a valid DiscordEnum")

    >>> PatchedEnum('FOO')  # 0.4184936599999993 seconds
    <PatchedEnum.FOO: 'FOO'>

    >>> QratorEnum('FOO')  # 0.3658666150000016 seconds
    <QratorEnum.FOO: FOO>

    >>> DiscordEnum('FOO')  # 0.22182812700000198 seconds
    <DiscordEnum.FOO: 'FOO'>

    >>> PatchedEnum(PatchedEnum.FOO)  # 1.023710457 seconds
    <PatchedEnum.FOO: 'FOO'>

    >>> try:     QratorEnum(QratorEnum.FOO) except: pass  # 1.7904693409999979 seconds
    ValueError('Value QratorEnum.FOO is not found in this enum type declaration')

    >>> try:     DiscordEnum(DiscordEnum.FOO) except: pass  # 1.950326038 seconds
    ValueError("<DiscordEnum.FOO: 'FOO'> is not a valid DiscordEnum")

    >>> PatchedEnum['FOO']  # 0.16261694599999998 seconds
    <PatchedEnum.FOO: 'FOO'>

    >>> QratorEnum['FOO']  # 0.19534894699999938 seconds
    <QratorEnum.FOO: FOO>

    >>> DiscordEnum['FOO']  # 0.16827563799999723 seconds
    <DiscordEnum.FOO: 'FOO'>


QratorEnum    :   3.849407 seconds in total,   0.589986 average (Fastest)
BuiltinEnum   :   8.185403 seconds in total,   0.917495 average, slower than QratorEnum by x  1.555114 (in average)
PatchedEnum   :   4.222823 seconds in total,   0.621179 average, slower than QratorEnum by x  1.052871 (in average)
DiscordEnum   :   3.867893 seconds in total,   0.508047 average, slower than QratorEnum by x  0.861118 (in average)


MISC:
Testing with 1000000 repeats:

    >>> sys.getsizeof(BuiltinEnum)  # 0.3463457640000023 seconds
    1064

    >>> sys.getsizeof(BuiltinEnum.FOO)  # 0.3540191010000022 seconds
    48

    >>> for member in BuiltinEnum: pass  # 1.026327246000001 seconds
    

    >>> dir(BuiltinEnum)  # 0.6587029179999995 seconds
    ['BAR', 'FOO', '__class__', '__doc__', '__members__', '__module__']

    >>> repr(BuiltinEnum)  # 0.5787854760000002 seconds
    "<enum 'BuiltinEnum'>"

Testing with 1000000 repeats:

    >>> sys.getsizeof(PatchedEnum)  # 0.2629475889999995 seconds
    1064

    >>> sys.getsizeof(QratorEnum)  # 0.27360790599999874 seconds
    896

    >>> sys.getsizeof(DiscordEnum)  # 0.26768483700000445 seconds
    1064

    >>> sys.getsizeof(PatchedEnum.FOO)  # 0.24858644300000066 seconds
    96

    >>> sys.getsizeof(QratorEnum.FOO)  # 0.25667530100000135 seconds
    56

    >>> sys.getsizeof(DiscordEnum.FOO)  # 0.26735041700000295 seconds
    56

    >>> for member in PatchedEnum: pass  # 0.3077472499999985 seconds
    

    >>> for member in QratorEnum: pass  # 0.30430272899999977 seconds
    

    >>> for member in DiscordEnum: pass  # 0.6717291199999949 seconds
    

    >>> dir(PatchedEnum)  # 0.533946641 seconds
    ['BAR', 'FOO', '__class__', '__doc__', '__members__', '__module__']

    >>> dir(QratorEnum)  # 5.432161248 seconds
    ['BAR', 'FOO', '__annotations__', '__call__', '__class__', '__copy__', '__deepcopy__', '__delattr__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__slots__', '__str__', '__subclasshook__', '_finalized', '_value_to_instance_map', 'name', 'value']

    >>> dir(DiscordEnum)  # 5.520358109 seconds
    ['BAR', 'FOO', '__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_enum_member_map_', '_enum_member_names_', '_enum_value_map_', 'try_value']

    >>> repr(PatchedEnum)  # 0.47733354700000064 seconds
    "<enum 'PatchedEnum'>"

    >>> repr(QratorEnum)  # 0.2783718430000022 seconds
    "<class '__main__.QratorEnum'>"

    >>> repr(DiscordEnum)  # 0.4721173049999976 seconds
    "<enum 'DiscordEnum'>"


PatchedEnum   :   1.830561 seconds in total,   0.348315 average (Fastest)
BuiltinEnum   :   2.964181 seconds in total,   0.544761 average, slower than PatchedEnum by x  1.563989 (in average)
QratorEnum    :   6.545119 seconds in total,   0.503365 average, slower than PatchedEnum by x  1.445144 (in average)
DiscordEnum   :   7.199240 seconds in total,   0.660060 average, slower than PatchedEnum by x  1.895008 (in average)


TOTAL TIME:

PatchedEnum   :   6.742196 seconds in total,   0.262762 average (Fastest)
BuiltinEnum   :  13.131719 seconds in total,   0.512510 average, slower than PatchedEnum by x  1.950473 (in average)
QratorEnum    :  11.291641 seconds in total,   0.314224 average, slower than PatchedEnum by x  1.195849 (in average)
DiscordEnum   :  12.109869 seconds in total,   0.347651 average, slower than PatchedEnum by x  1.323064 (in average)
```