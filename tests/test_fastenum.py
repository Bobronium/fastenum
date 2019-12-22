import subprocess
import sys
from enum import Enum, EnumMeta, Flag

import pytest

import fastenum
from fastenum import EnumPatch, EnumMetaPatch

assert fastenum.enabled


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
    assert fastenum.enabled
    fastenum.disable()

    assert hasattr(EnumMeta, '__getattr__')
    assert 'name' in Enum.__dict__
    assert 'value' in Enum.__dict__

    assert Enum.__new__ is not EnumPatch.__new__
    assert Enum.__dict__['__new__'] is EnumPatch.__original_attrs__['__new__']
    assert EnumMeta.__new__ is not EnumMetaPatch.__new__
    assert EnumMeta.__dict__['__new__'] is EnumMetaPatch.__original_attrs__['__new__']

    fastenum.enable()

    assert not hasattr(EnumMeta, '__getattr__')
    assert 'name' not in Enum.__dict__
    assert 'value' not in Enum.__dict__

    assert Enum.__new__ is EnumPatch.__to_update__['__new__']
    assert EnumMeta.__new__ is EnumMetaPatch.__to_update__['__new__']


def test_non_named_members_have_attrs():
    assert fastenum.enabled
    fastenum.disable()

    class Foo(Flag):
        a = 1
        b = 2

    fake_member = Foo._create_pseudo_member_(3)
    assert 'name' not in fake_member.__dict__
    assert 'value' not in fake_member.__dict__
    Foo._value2member_map_[fake_member._value_] = fake_member

    fastenum.enable()
    assert 'name' in fake_member.__dict__
    assert 'value' in fake_member.__dict__


def test_attrs_set():
    class Foo(Flag):
        a = 1
        b = 2

    Foo.a._value_ = 42
    assert Foo.a.value == 42


@pytest.mark.parametrize('python', ('python3.6', 'python3.7', 'python3.8'))
def test_builtin_tests(python):
    try:
        print(f'\nRunning {python} tests', file=sys.stderr)
        result = subprocess.run([python, f'builtin_test.py'])
    except FileNotFoundError as e:
        return pytest.skip(f'Unable to run test with {python}, {str(e)}')

    assert result.returncode == 0, f'Tests failed in {python}'
