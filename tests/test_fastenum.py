import os
import subprocess
import sys
import warnings

import pytest

from fastenum import (
    Enum,
    IntEnum,
    IntFlag,
    Flag,
    BuiltinEnum,
    BuiltinIntEnum,
    BuiltinFlag,
    BuiltinIntFlag,
    BuiltinEnumMeta,
    auto,
)


class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3


class Shape(Enum):
    SQUARE = 2
    DIAMOND = 1
    CIRCLE = 3
    ALIAS_FOR_SQUARE = 2


def test_inheritance():
    assert issubclass(Enum, BuiltinEnum)
    assert issubclass(BuiltinEnum, Enum)

    assert isinstance(Color.RED, BuiltinEnum)
    assert isinstance(Color.RED, Enum)

    assert issubclass(Flag, BuiltinEnum)
    assert issubclass(Flag, BuiltinFlag)
    assert issubclass(BuiltinFlag, Flag)
    assert not issubclass(BuiltinEnum, Flag)

    class Foo(Flag):
        a = 1

    assert isinstance(Foo.a, BuiltinFlag)

    assert issubclass(IntEnum, BuiltinIntEnum)
    assert issubclass(IntFlag, BuiltinIntFlag)


def test_basics():
    assert str(Color.RED) == 'Color.RED'
    assert repr(Color.RED) == '<Color.RED: 1>'
    assert type(Color.RED) is Color
    assert isinstance(Color.GREEN, Color)


def test_iteration():
    class Shake(Enum):
        VANILLA = 7
        CHOCOLATE = 4
        COOKIES = 9
        MINT = 3

    for shake, name in zip(Shake, ('VANILLA', 'CHOCOLATE', 'COOKIES', 'MINT')):
        assert isinstance(shake, Shake)
        assert str(shake) == f'Shake.{name}'


def test_hashable():
    apples = {}
    apples[Color.RED] = 'red delicious'
    apples[Color.GREEN] = 'granny smith'
    assert apples == {Color.RED: 'red delicious', Color.GREEN: 'granny smith'}


def test_access():
    assert repr(Color(1)) == '<Color.RED: 1>'
    assert repr(Color(3)) == '<Color.BLUE: 3>'
    assert repr(Color['RED']) == '<Color.RED: 1>'
    assert repr(Color['GREEN']) == '<Color.GREEN: 2>'

    member = Color.RED
    assert member.name == 'RED'
    assert member.value == 1


def test_duplicate_error():
    with pytest.raises(TypeError, match="Attempted to reuse key: 'SQUARE'"):
        class Shape(Enum):
            SQUARE = 2
            SQUARE = 3


def test_allow_duplicate_values():
    assert repr(Shape.SQUARE) == '<Shape.SQUARE: 2>'
    assert repr(Shape.ALIAS_FOR_SQUARE) == '<Shape.SQUARE: 2>'
    assert repr(Shape(2)) == '<Shape.SQUARE: 2>'


def test_unique_decorator():
    from enum import unique
    with pytest.raises(ValueError, match="duplicate values found in <enum 'Mistake'>: FOUR -> THREE"):
        @unique
        class Mistake(Enum):
            ONE = 1
            TWO = 2
            THREE = 3
            FOUR = 3

    from fastenum import unique
    with pytest.raises(ValueError, match="duplicate values found in <enum 'Mistake'>: FOUR -> THREE"):
        @unique
        class Mistake(Enum):
            ONE = 1
            TWO = 2
            THREE = 3
            FOUR = 3


def test_automatic_values():
    from enum import Enum, auto

    class Color(Enum):
        RED = auto()
        BLUE = auto()
        GREEN = auto()

    assert [member.value for member in Color] == [1, 2, 3]

    class AutoName(Enum):
        def _generate_next_value_(name, start, count, last_values):
            return name

    class Ordinal(AutoName):
        NORTH = auto()
        SOUTH = auto()
        EAST = auto()
        WEST = auto()

    assert Ordinal.NORTH.value == 'NORTH'
    assert all(member.name == member.value for member in Ordinal)


def test_iteratio_members_():
    assert list(Shape.__members__.items()) == [
        (Shape.SQUARE.name, Shape.SQUARE),
        (Shape.DIAMOND.name, Shape.DIAMOND),
        (Shape.CIRCLE.name, Shape.CIRCLE),
        ('ALIAS_FOR_SQUARE', Shape.SQUARE)]


def test_comparison():
    assert Color.RED is Color.RED
    assert Color.RED is not Color.BLUE

    with pytest.raises(TypeError, match="'<' not supported between instances of 'Color' and 'Color'"):
        assert Color.RED < Color.BLUE

    assert not Color.BLUE == Color.RED
    assert Color.BLUE != Color.RED
    assert Color.BLUE == Color.BLUE
    assert not Color.BLUE == 2


def test_subclassing():
    with pytest.raises(TypeError, match='Cannot extend enumerations'):
        class MoreColor(Color):
            pink = 17

    class Foo(Enum):
        def some_behavior(self):
            pass

    class Bar(Foo):
        happy = 1
        sad = 2


def test_pickle():
    from pickle import dumps, loads
    assert Color.RED is loads(dumps(Color.RED))


def test_functional_api():
    Animal = Enum('Animal', 'ANT BEE CAT DOG')
    assert repr(Animal) == "<enum 'Animal'>"
    assert repr(Animal.ANT) == '<Animal.ANT: 1>'
    assert Animal.ANT.value == 1


def test_int_enum():
    class Shape(IntEnum):
        CIRCLE = 1
        SQUARE = 2

    class Request(IntEnum):
        POST = 1
        GET = 2

    assert Shape != 1
    assert Shape.CIRCLE == 1
    assert Shape.CIRCLE == Request.POST

    assert Shape.CIRCLE != Color.RED


def test_int_flag():
    class Perm(IntFlag):
        R = 4
        W = 2
        X = 1

    assert repr(Perm.R | Perm.W) == '<Perm.R|W: 6>'
    assert Perm.R + Perm.W == 6
    RW = Perm.R | Perm.W
    assert Perm.R in RW

    assert repr(Perm.R & Perm.X) == '<Perm.0: 0>'
    assert not bool(Perm.R & Perm.X)

    assert repr(Perm.X | 8) == '<Perm.8|X: 9>'


def test_flag():
    class Color(Flag):
        RED = auto()
        BLUE = auto()
        GREEN = auto()

    assert repr(Color.RED & Color.GREEN) == '<Color.0: 0>'
    assert not bool(Color.RED & Color.GREEN)

    class Color(Flag):
        RED = auto()
        BLUE = auto()
        GREEN = auto()
        WHITE = RED | BLUE | GREEN

    assert repr(Color.WHITE) == '<Color.WHITE: 7>'

    class Color(Flag):
        BLACK = 0
        RED = auto()
        BLUE = auto()
        GREEN = auto()

    assert repr(Color.BLACK) == '<Color.BLACK: 0>'
    assert not bool(Color.BLACK)


def test_edge_cases():
    class NoValue(Enum):
        def __repr__(self):
            return '<%s.%s>' % (self.__class__.__name__, self.name)

    class Color(NoValue):
        RED = object()
        GREEN = object()
        BLUE = object()

    assert repr(Color.GREEN) == '<Color.GREEN>'

    class Color(NoValue):
        RED = 'stop'
        GREEN = 'go'
        BLUE = 'too fast!'

    assert repr(Color.GREEN) == '<Color.GREEN>'
    assert Color.GREEN.value == 'go'

    class AutoNumber(NoValue):
        def __new__(cls):
            value = len(cls.__members__) + 1
            obj = object.__new__(cls)
            obj._value_ = value
            return obj

    class Color(AutoNumber):
        RED = ()
        GREEN = ()
        BLUE = ()

    assert repr(Color.GREEN) == '<Color.GREEN>'

    assert Color.GREEN.value == 2


def test_name_value_shadowing():
    class Foo(Enum):
        name = 1
        value = 2

    assert isinstance(Foo.name, Foo)
    assert isinstance(Foo.value, Foo)
    assert Foo.name.name == 'name'
    assert Foo.name.value == 1
    assert Foo.value.name == 'value'
    assert Foo.value.value == 2


def test_patched_enum():
    assert not hasattr(BuiltinEnumMeta, '__getattr__')
    assert not hasattr(BuiltinEnum, 'name')
    assert not hasattr(BuiltinEnum, 'value')


def test_builtin_tests():
    for version in 6, 7, 8:
        test_cmd = [f'python3.{version}', '-m', 'unittest', f'tests.builtin_tests.test_3{version}']
        try:
            print(f'\nRUNNING ' + ' '.join(test_cmd), file=sys.stderr)
            subprocess.run(test_cmd, check=True)
        except FileNotFoundError as e:
            warnings.warn(f'Unable to run test with {test_cmd}, {str(e)}')
            continue
