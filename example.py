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

from abc import abstractmethod
from main import Contract


class Stack(Contract):
    def __invariant__(self):
        assert self.size() >= 0, f"Size should be positive but is {self.size()}"

    @abstractmethod
    def push(self, e):
        def __ensure__(self, ret, old, e):
            assert self.size() == old.size() + 1, (
                f"Increase stack size. "
                f"Should be {self.size()} but is {old.size()}")
            assert self.top() == e, (f"New top of stack should be {e} "
                                     f"but is {self.top()}")

    @abstractmethod
    def pop(self):
        def __require__(self):
            assert self.size() >= 1, "Pop from empty stack"

        def __ensure__(self, ret, old):
            assert self.size() == old.size() - 1, (
                f"Decrease stack size. Should be {old.size() - 1} "
                f"but is {self.size()}")
            assert ret == old.top(), (
                f"Return {old.top()} should be old top of stack ({ret})")

    @abstractmethod
    def top(self):
        def __require__(self):
            assert self.size() >= 1, "No top: empty stack"

    @abstractmethod
    def size(self):
        pass


class StackImpl(Stack):
    def __init__(self):
        self._arr = []
        self._size = 0

    def push(self, e):
        self._arr.append(e)
        self._size += 1

    def pop(self):
        self._size -= 1
        return self._arr.pop()

    def top(self):
        return self._arr[self._size - 1]

    def size(self):
        return self._size


class WrongStackImpl(Stack):
    def __init__(self):
        self._arr = []
        self._size = 0
        self.__skip_assertions__ = False

    def push(self, e):
        self._arr.append(e)
        self._size += 1

    def pop(self):
        # self._size -= 1
        return self._arr.pop()

    def top(self):
        return self._arr[self._size - 1]

    def size(self):
        return self._size


class EvenStack(Contract):
    def __invariant__(self):
        assert self.size() == 0 or self.top() % 2 == 0, f"Top should be even but was {self.top()}"


class EvenStackImpl(StackImpl, EvenStack):
    pass


