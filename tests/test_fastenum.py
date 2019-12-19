import subprocess
import sys
import warnings
from enum import Enum, EnumMeta

import fastenum
from fastenum.fastenum import PatchedEnum, PatchedEnumMeta

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
    assert not Enum.__is_fast__()

    assert hasattr(EnumMeta, '__getattr__')
    assert 'name' in Enum.__dict__
    assert 'value' in Enum.__dict__

    assert Enum.__new__ is not PatchedEnum.__attrs_to_patch__['__new__']
    assert Enum.__new__ is PatchedEnum.__original_attrs__['__new__']
    assert EnumMeta.__new__ is not PatchedEnumMeta.__attrs_to_patch__['__new__']
    assert EnumMeta.__new__ is PatchedEnumMeta.__original_attrs__['__new__']

    fastenum.enable()
    assert Enum.__is_fast__()

    assert not hasattr(EnumMeta, '__getattr__')
    assert 'name' not in Enum.__dict__
    assert 'value' not in Enum.__dict__

    assert Enum.__new__ is PatchedEnum.__attrs_to_patch__['__new__']
    assert EnumMeta.__new__ is PatchedEnumMeta.__attrs_to_patch__['__new__']


def test_builtin_tests():
    for version in 6, 7, 8:
        test_cmd = [f'python3.{version}', '-m', 'unittest', f'tests.builtin_tests.test_3{version}']
        try:
            print(f'\nRUNNING ' + ' '.join(test_cmd), file=sys.stderr)
            subprocess.run(test_cmd, check=True)
        except FileNotFoundError as e:
            warnings.warn(f'Unable to run test with {test_cmd}, {str(e)}')
            continue
