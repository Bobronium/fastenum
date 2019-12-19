import math
import sys
import time
from enum import Enum
from timeit import timeit
from typing import Iterable, Dict, List, Tuple, Union, TypeVar

import discordenum
import qratorenum

import fastenum

assert sys  # used in some cases, passed in through globals()

TRY_EXCEPT_BLOCK_TMPL = 'try:\n    {expr}\nexcept: pass'

assert fastenum.enabled


def geomean(numbers) -> float:
    return math.exp(math.fsum(math.log(x) for x in numbers) / len(numbers))


def calculate_difference(time_elapsed: Dict[type, List[float]]) -> str:
    time_elapsed = time_elapsed.copy()
    fastest = min(time_elapsed, key=lambda i: sum(time_elapsed[i]))
    fastest_time = time_elapsed.pop(fastest)
    average_fastest = geomean(fastest_time)

    result = (
        f'\n{fastest.__name__:<14}: {sum(fastest_time):10f} seconds in total, {average_fastest:10f} average (Fastest)'
    )
    for type_, elapsed in time_elapsed.items():
        average = geomean(elapsed)
        result += (
            f'\n{type_.__name__:<14}: {sum(elapsed):10f} seconds in total, {average:10f} average, '
            f'slower than {fastest.__name__} by x{average / average_fastest:10f} (in average)'
        )

    return result


def eval_and_timeit(code, global_ns, number, setup='pass', **local_ns):
    result = None
    exception = None
    try:
        result = eval(code, global_ns, local_ns)
    except SyntaxError:
        try:
            exec(code, global_ns, local_ns)
        except SyntaxError:
            raise
        except Exception as e:
            exception = e
    except Exception as e:
        exception = e

    if exception is not None:
        code = TRY_EXCEPT_BLOCK_TMPL.format(expr=code)
        return code, exception, timeit(code, setup, globals=global_ns, number=number)
    return code, result, timeit(code, setup, globals=global_ns, number=number)


T = TypeVar('T')


def test(
        *objects: T,
        expressions: Iterable[Union[str, Tuple[str, str]]],
        number: int = 1000000,
        group_by_objects: bool = False,
        format_mapping: Dict[str, str] = None,
        pause_interval=0,
        **globals_ns
) -> Dict[T, List[float]]:
    """
    :param objects: objects to test1
    :param expressions: expressions to test1 on objects
    :param number: number of repeats for each expression (passed in timeit)
    :param group_by_objects: if True, expressions will be evaluated and tested in order of objects, else of expressions
    :param format_mapping: mapping to format str where keys is keys in str and values is attrs of current object
    :param pause_interval: interval between tests
    :param globals_ns: namespace for test1

    :return: dict with objects as keys and total time elapsed by them as values

    >>> class Foo:
    ...    BAR = 'baz'

    >>> class Bar:
    ...     @property
    ...     def BAR(self):
    ...         return 'baz'

    >>> test(Foo, Bar, expressions=('{obj}().BAR', '{obj}().BAR = 1}'), Foo=Foo, Bar=Bar)
    Testing with 1000000 repeats:

        >>> Foo().BAR  # 0.1405952029999753 seconds
        'baz'

        >>> Bar().BAR  # 0.27527517399721546 seconds
        'baz'

        >>> Foo().BAR = 1  # 0.20322119499905966 seconds


        >>> try:     Bar().BAR = 1 except: pass  # 0.41546584199750214 seconds
        AttributeError("can't set attribute",)
    """
    print(f'Testing with {number} repeats:\n')

    if group_by_objects:
        obj_expressions = ((obj, expression) for obj in objects for expression in expressions)
    else:  # by expressions
        obj_expressions = ((obj, expression) for expression in expressions for obj in objects)

    if format_mapping is None:
        format_mapping = {'obj': '__name__'}  # expression.format(obj=obj.__name__)

    time_elapsed = {}
    for obj, expression in obj_expressions:
        if not isinstance(expression, str):
            expression, setup = expression
        else:
            setup = 'pass'

        formatting = {key: getattr(obj, attr) for key, attr in format_mapping.items()}
        code = expression.format(**formatting)
        setup = setup.format(**formatting)

        time.sleep(pause_interval)
        code, result, elapsed = eval_and_timeit(code, setup=setup, number=number, global_ns=globals_ns)

        time_elapsed.setdefault(obj, []).append(elapsed)

        code = code.replace('\n', ' ')
        result = repr(result) if result is not None else ''
        print(f'    >>> {code}  # {elapsed} seconds\n    {result}\n')

    return time_elapsed


fastenum.disable()


class BuiltinEnum(str, Enum):
    FOO = 'FOO'
    BAR = 'BAR'


fastenum.enable()


class PatchedEnum(str, Enum):
    FOO = 'FOO'
    BAR = 'BAR'


class QratorEnum(str, metaclass=qratorenum.FastEnum):
    FOO: 'QratorEnum' = 'FOO'
    BAR: 'QratorEnum' = 'BAR'


class DiscordEnum(str, discordenum.Enum):
    FOO = 'FOO'
    BAR = 'BAR'


if __name__ == '__main__':
    CASES = dict(
        ATTR_ACCESS=(
            '{obj}.FOO',
            "{obj}.FOO.value",
        ),
        INHERITANCE=(
            'issubclass({obj}, Enum)',
            'isinstance({obj}.FOO, Enum)',
            'isinstance({obj}.FOO, {obj})',
            'isinstance({obj}.FOO, str)',
        ),
        TRYING_VALUES=(
            "{obj}.FOO = 'new'",
            "{obj}('unknown')",
            "{obj}('FOO')",
            '{obj}({obj}.FOO)',
            "{obj}['FOO']"
        ),
        MISC=(
            'sys.getsizeof({obj})',
            'sys.getsizeof({obj}.FOO)',
            'for member in {obj}: pass',
            'dir({obj})',
            'repr({obj})',
        )
    )

    candidates = (
        PatchedEnum,
        QratorEnum,
        DiscordEnum,
    )

    total_time_elapsed = {}
    for name, expr in CASES.items():
        print(f'\n\n{name}:')

        # Fast enum also affects builtin enums speed
        fastenum.disable()
        time_info = test(BuiltinEnum, expressions=expr, group_by_objects=False, **globals())
        fastenum.enable()

        time_info.update(test(*candidates, expressions=expr, group_by_objects=False, **globals()))
        for t, elapsed_ in time_info.items():
            total_time_elapsed.setdefault(t, []).extend(elapsed_)
        print((calculate_difference(time_info)))
    print(f'\n\nTOTAL TIME:')
    print((calculate_difference(total_time_elapsed)))
