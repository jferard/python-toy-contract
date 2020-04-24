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
from main import Contract


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
        class A(metaclass=Contract):
            def f(self):
                def __require__(self):
                    pass

        with self.assertRaisesRegex(AssertionError,
                               "Use __require_else__ instead of __require__ in"):
            class B(A, metaclass=Contract):
                def f(self):
                    def __require__(self):
                        pass

    def test_no_require(self):
        with self.assertRaisesRegex(AssertionError,
                               "Missing __require__ in"):
            class A(metaclass=Contract):
                def f(self):
                    def __require_else__(self):
                        pass

    def test_two_ensures(self):
        class A(metaclass=Contract):
            def f(self):
                def __ensure__(self):
                    pass

        with self.assertRaisesRegex(AssertionError,
                               "Use __ensure_then__ instead of __ensure__ in"):
            class B(A, metaclass=Contract):
                def f(self):
                    def __ensure__(self):
                        pass

    def test_no_ensure(self):
        with self.assertRaisesRegex(AssertionError,
                               "Missing __ensure__ in"):
            class A(metaclass=Contract):
                def f(self):
                    def __ensure_then__(self):
                        pass

if __name__ == '__main__':
    unittest.main()
