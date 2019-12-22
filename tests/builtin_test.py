import sys
import unittest
from test import test_enum, test_re, test_inspect, test_dynamicclassattribute

TEST_MODULES = test_enum, test_re, test_inspect, test_dynamicclassattribute

expected_help_output_with_docs = """\
Help on class Color in module %s:

class Color(enum.Enum)
 |  Color(value, names=None, *, module=None, qualname=None, type=None, start=1)
 |\x20\x20
 |  An enumeration.
 |\x20\x20
 |  Method resolution order:
 |      Color
 |      enum.Enum
 |      builtins.object
 |\x20\x20
 |  Data and other attributes defined here:
 |\x20\x20
 |  blue = <Color.blue: 3>
 |\x20\x20
 |  green = <Color.green: 2>
 |\x20\x20
 |  red = <Color.red: 1>
 |\x20\x20
 |  ----------------------------------------------------------------------
 |  Readonly properties inherited from enum.EnumMeta:
 |\x20\x20
 |  __members__
 |      Returns a mapping of member name->value.
 |\x20\x20\x20\x20\x20\x20
 |      This mapping lists all enum members, including aliases. Note that this
 |      is a read-only view of the internal mapping."""


if sys.version_info < (3, 8):
    expected_help_output_with_docs = expected_help_output_with_docs.replace(
        'Readonly properties inherited from enum.EnumMeta:',
        'Data descriptors inherited from enum.EnumMeta:'
    )
if sys.version_info < (3, 7):
    expected_help_output_with_docs = expected_help_output_with_docs.replace(
        '\n |  Color(value, names=None, *, module=None, qualname=None, type=None, start=1)\n |\x20\x20',
        ''
    )


def test_inspect_getmembers(self):
    values = dict((
        ('__class__', test_enum.EnumMeta),
        ('__doc__', 'An enumeration.'),
        ('__members__', self.Color.__members__),
        ('__module__', test_enum.__name__),
        ('blue', self.Color.blue),
        ('green', self.Color.green),
        ('red', self.Color.red),
    ))
    result = dict(test_enum.inspect.getmembers(self.Color))
    self.assertEqual(values.keys(), result.keys())
    failed = False
    for k in values.keys():
        if result[k] != values[k]:
            print()
            print('\n%s\n     key: %s\n  result: %s\nexpected: %s\n%s\n' %
                  ('=' * 75, k, result[k], values[k], '=' * 75), sep='')
            failed = True
    if failed:
        self.fail("result does not equal expected, see print above")


def test_inspect_classify_class_attrs(self):
    # indirectly test __objclass__
    from inspect import Attribute
    values = [
            Attribute(name='__class__', kind='data',
                defining_class=object, object=test_enum.EnumMeta),
            Attribute(name='__doc__', kind='data',
                defining_class=self.Color, object='An enumeration.'),
            Attribute(name='__members__', kind='property',
                defining_class=test_enum.EnumMeta, object=test_enum.EnumMeta.__members__),
            Attribute(name='__module__', kind='data',
                defining_class=self.Color, object=test_enum.__name__),
            Attribute(name='blue', kind='data',
                defining_class=self.Color, object=self.Color.blue),
            Attribute(name='green', kind='data',
                defining_class=self.Color, object=self.Color.green),
            Attribute(name='red', kind='data',
                defining_class=self.Color, object=self.Color.red),
            ]
    values.sort(key=lambda item: item.name)
    result = list(test_enum.inspect.classify_class_attrs(self.Color))
    result.sort(key=lambda item: item.name)
    failed = False
    for v, r in zip(values, result):
        if r != v:
            print('\n%s\n%s\n%s\n%s\n' % ('=' * 75, r, v, '=' * 75), sep='')
            failed = True
    if failed:
        self.fail("result does not equal expected, see print above")


class TestSetClassAttr(unittest.TestCase):
    def test_set_class_attr(self):
        class Foo:
            def __init__(self, value):
                self._value = value
                self._spam = 'spam'

            @test_dynamicclassattribute.DynamicClassAttribute
            def value(self):
                return self._value

            spam = test_dynamicclassattribute.DynamicClassAttribute(
                lambda s: s._spam,
                alias='my_shiny_spam'
            )

        self.assertFalse(hasattr(Foo, 'value'))
        self.assertFalse(hasattr(Foo, 'name'))

        foo_bar = Foo('bar')
        value_desc = Foo.__dict__['value']
        value_desc.set_class_attr(Foo, foo_bar)
        self.assertIs(Foo.value, foo_bar)
        self.assertEqual(Foo.value.value, 'bar')

        foo_baz = Foo('baz')
        Foo.my_shiny_spam = foo_baz
        self.assertIs(Foo.spam, foo_baz)
        self.assertEqual(Foo.spam.spam, 'spam')


def run_tests():
    loader = unittest.TestLoader()
    suites = [
        loader.loadTestsFromModule(module) for module in TEST_MODULES
    ]
    result = unittest.TextTestRunner().run(loader.suiteClass(suites))
    if result.failures or result.errors:
        sys.exit(1)


orig_test_inspect_getmembers = test_enum.TestStdLib.test_inspect_getmembers
orig_test_inspect_classify_class_attrs = test_enum.TestStdLib.test_inspect_classify_class_attrs
orig_expected_help_output_with_docs = test_enum.expected_help_output_with_docs

if __name__ == '__main__':
    # run_tests()  # if tests fail here only if something was wrong before patch
    import fastenum
    assert fastenum.enabled

    test_enum.TestStdLib.test_inspect_getmembers = test_inspect_getmembers
    test_enum.TestStdLib.test_inspect_classify_class_attrs = test_inspect_classify_class_attrs
    test_enum.expected_help_output_with_docs = expected_help_output_with_docs
    test_dynamicclassattribute.TestSetClassAttr = TestSetClassAttr

    run_tests()

    fastenum.disable()
    assert not fastenum.enabled

    test_enum.TestStdLib.test_inspect_getmembers = orig_test_inspect_getmembers
    test_enum.TestStdLib.test_inspect_classify_class_attrs = orig_test_inspect_classify_class_attrs
    test_enum.expected_help_output_with_docs = orig_expected_help_output_with_docs
    del test_dynamicclassattribute.TestSetClassAttr

    run_tests()
