# coding: utf-8
"""
Python Toy Contract.
(C) J. Férard 2020.

 Python Toy Contract is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Python Toy Contract is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import unittest
from example import EvenStackImpl, StackImpl, WrongStackImpl
from main import ContractMeta, Contract


class ExampleTestCase(unittest.TestCase):
    def test_empty_stack(self):
        s = StackImpl()
        with self.assertRaises(AssertionError, msg="Pop from empty stack"):
            s.pop()

    def test_wrong_implementation(self):
        s = WrongStackImpl()
        s.push(1)
        with self.assertRaises(AssertionError,
                               msg="Decrease stack size. Should be 0 but is 1"):
            s.pop()

    def test_even_stack_0(self):
        s = EvenStackImpl()
        s.push(0)

    def test_even_stack_1(self):
        s = EvenStackImpl()
        with self.assertRaises(AssertionError,
                               msg="Top should be even but was 1"):
            s.push(1)


class TestClasses(unittest.TestCase):
    def test_two_requires(self):
        class A(metaclass=ContractMeta):
            def f(self):
                def __require__(self):
                    pass

        with self.assertRaisesRegex(AssertionError,
                                    "Use __require_else__ instead of __require__ in"):
            class B(A):
                def f(self):
                    def __require__(self):
                        pass

    def test_no_require(self):
        with self.assertRaisesRegex(AssertionError,
                                    "Missing __require__ in"):
            class A(metaclass=ContractMeta):
                def f(self):
                    def __require_else__(self):
                        pass

    def test_require_and_else(self):
        with self.assertRaisesRegex(
                AssertionError,
                "Use either __require__ or __require_else__ in"):
            class A(metaclass=ContractMeta):
                def f(self):
                    def __require__(self):
                        pass

                    def __require_else__(self):
                        pass

    def test_two_ensures(self):
        class A(metaclass=ContractMeta):
            def f(self):
                def __ensure__(self):
                    pass

        with self.assertRaisesRegex(AssertionError,
                                    "Use __ensure_then__ instead of __ensure__ in"):
            class B(A):
                def f(self):
                    def __ensure__(self):
                        pass

    def test_no_ensure(self):
        with self.assertRaisesRegex(AssertionError,
                                    "Missing __ensure__ in"):
            class A(metaclass=ContractMeta):
                def f(self):
                    def __ensure_then__(self):
                        pass

    def test_ensure_and_then(self):
        with self.assertRaisesRegex(AssertionError,
                                    "Use either __ensure__ or __ensure_then__ in"):
            class A(metaclass=ContractMeta):
                def f(self):
                    def __ensure__(self):
                        pass

                    def __ensure_then__(self):
                        pass

    def test_init(self):
        class A(Contract):
            def __invariant__(self):
                assert self.x > 0, "Variable x should be positive"

            def __init__(self):
                self.x = -1

        with self.assertRaisesRegex(AssertionError,
                                    "Variable x should be positive"):
            A()

    def test_no_paranoid(self):
        class A(Contract):
            __paranoid__ = False

            def __invariant__(self):
                assert self._x > 0, "Variable x should be positive"

            def __init__(self):
                self._x = 1

            def inc(self):
                self._x += 1

        a = A()
        a._x = 0  # break the invariant
        a.inc()   # still ok

    def test_paranoid(self):
        class A(Contract):
            def __invariant__(self):
                assert self._x > 0, "Variable x should be positive"

            def __init__(self):
                self._x = 1

            def inc(self):
                self._x += 1

        a = A()
        a._x = 0  # break the invariant
        with self.assertRaisesRegex(AssertionError,
                                    "Variable x should be positive"):
            a.inc()


if __name__ == '__main__':
    unittest.main()
