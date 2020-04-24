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

from abc import ABCMeta
from types import CodeType, FunctionType
from dataclasses import dataclass
from typing import (Callable, Sequence, Mapping, TypeVar, Generic, Optional,
                    Any, Iterable)
from copy import deepcopy
import logging

T = TypeVar('T')
OC = Optional[Callable]

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("Python Toy Contract")
logger.setLevel(logging.DEBUG)
logger.debug("Logger on.")


@dataclass
class Localized(Generic[T]):
    value: T
    origin: Optional[Any] = None

    def __bool__(self):
        return bool(self.value)


@dataclass
class MethodInfo:
    name: str
    method: Callable
    requires: Sequence[Localized[Callable]]
    ensures: Sequence[Localized[Callable]]

    @staticmethod
    def from_method(name: str, method: Callable,
                    methods: Sequence[Localized[OC]]
                    ) -> "MethodInfo":
        return _MethodInfoFactory(name, method, methods).create()


class _MethodInfoFactory:
    def __init__(self, name: str, method: Callable,
                 methods: Sequence[Localized[OC]]):
        self._name = name
        self._method = method
        self._methods = methods

    def create(self):
        requires = self._extract_assertions("__require__", "__require_else__")
        ensures = self._extract_assertions("__ensure__", "__ensure_then__")
        return MethodInfo(self._name, self._method, requires, ensures)

    def _extract_assertions(self, assertion_name: str,
                            child_assertion_name: str
                            ) -> Sequence[Localized[Callable]]:
        logger.debug(("...Extract assertions `%s` and `%s` "
                      "from methods named `%s`"),
                     assertion_name, child_assertion_name, self._name)
        localized_assertions = []
        it = iter(reversed(self._methods))
        for node in it:
            assertion_method = self._find_nested_method(node.value,
                                                        assertion_name)
            if assertion_method is None:
                child_method = self._find_nested_method(node.value,
                                                        child_assertion_name)
                assert not child_method, (
                    f"Missing {assertion_name} in {node.origin}")
            else:
                localized_assertions.append(Localized(
                    value=assertion_method,
                    origin=node.origin
                ))
                break

        for node in it:
            child_assertion_method = self._find_nested_method(
                node.value, child_assertion_name)
            if child_assertion_method is None:
                parent_method = self._find_nested_method(node.value,
                                                         assertion_name)
                assert not parent_method, (
                    f"Use {child_assertion_name} instead of "
                    f"{assertion_name} in {node.origin}")
            else:
                localized_assertions.append(Localized(
                    value=child_assertion_method,
                    origin=node.origin
                ))

        return localized_assertions

    @staticmethod
    def _find_nested_method(method: OC, nested_name: str) -> OC:
        if method is None:
            return None
        consts = method.__code__.co_consts
        for item in consts:
            if isinstance(item, CodeType) and item.co_name == nested_name:
                logger.debug(f"....Found assertion %s in %s", nested_name,
                             method)
                return FunctionType(item, globals())

        return None


@dataclass
class ClassContract:
    invariants: Sequence[Localized[OC]]
    method_info_by_name: Mapping[str, MethodInfo]

    @staticmethod
    def from_class(cls: type) -> "ClassContract":
        return _ClassContractFactory(cls).create()


class _ClassContractFactory:
    def __init__(self, cls: type):
        self._cls = cls

    def create(self) -> ClassContract:
        logger.debug(f".Analyse class hierarchy of %s", self._cls)
        logger.debug(f"..Extract invariants %s", self._cls)
        invariants = _ClassContractFactory._find_invariants(self._cls)
        logger.debug(f"..Extract pre/post conditions %s", self._cls)
        method_info_by_name = self._find_method_info_by_name()
        return ClassContract(invariants, method_info_by_name)

    @staticmethod
    def _find_invariants(cls: type) -> Sequence[Localized[Callable]]:
        invariants = []
        for c in cls.__mro__[:-1]:
            invariant = _ClassContractFactory._find_invariant(c)
            if invariant:
                logger.debug("...Found invariant in `%s`", c)
                invariants.append(
                    Localized(value=invariant,
                              origin=c))
        return invariants

    @staticmethod
    def _find_invariant(c: type) -> OC:
        return _ClassContractFactory.get_attr(c, "__invariant__")

    @staticmethod
    def get_attr(c, attr) -> Optional[Any]:
        try:
            return c.__getattribute__(c, attr)
        except AttributeError as e:
            return None

    def _find_method_info_by_name(self) -> Mapping[str, MethodInfo]:
        method_by_name = self._find_method_by_name()
        logger.debug(f"...Public methods by name: %s", method_by_name)
        methods_by_name = _ClassContractFactory._find_methods_by_name(
            method_by_name, self._cls)
        logger.debug(f"...Sequence of methods by name: %s", methods_by_name)
        return {name: MethodInfo.from_method(name, method,
                                             methods_by_name[name])
                for name, method in method_by_name.items()}

    def _find_method_by_name(self) -> Mapping[str, Callable]:

        method_by_name = {}
        for method_name in self._public_methods():
            method_by_name[method_name] = getattr(self._cls, method_name)
        return method_by_name

    def _public_methods(self) -> Iterable[str]:
        for method_name in dir(self._cls):
            if (not method_name.startswith("_") and
                    callable(getattr(self._cls, method_name))):
                yield method_name

    @staticmethod
    def _find_methods_by_name(method_by_name: Mapping[str, Callable], cls: type
                              ) -> Mapping[str, Sequence[Localized[Callable]]]:
        """"""
        methods_by_name = {}
        for name, method in method_by_name.items():
            methods_by_name[
                name] = [Localized(value=method,
                                   origin=cls)] + _ClassContractFactory._find_parent_methods(
                cls, name)
        return methods_by_name

    @staticmethod
    def _find_parent_methods(cls: type, name: str) -> Sequence[Localized[OC]]:
        """
        Find methods of given name. The starting class is `cls`.
        Just follow the MRO, skipping the current class, until we find a class
        having the method. If there is no class, the parents methods are an
        empty list. Else, we take the first method and append the parents
        methods recusively
        :param cls: the class
        :param name: the name of the method
        :return:
        """
        localized_methods = (
            Localized(value=_ClassContractFactory.get_attr(c, name),
                      origin=c) for c in cls.__mro__[1:])
        localized_method = next((lm for lm in localized_methods if lm.value
                                 is not None), None)
        if localized_method is None:
            return []
        else:
            return [localized_method
                    ] + _ClassContractFactory._find_parent_methods(
                localized_method.origin, name)


class Contract(ABCMeta):
    def __new__(mcs, name, bases, dict):
        logger.info(f"Create contracted/relaxed for class `{name}`")
        logger.debug(f"Create relaxed version")
        relaxed_bases = tuple([getattr(b, '__relaxed__', b) for b in bases])
        relaxed_D = ABCMeta.__new__(mcs, "relaxed_" + name, relaxed_bases, dict)
        logger.debug(f"Relaxed version created: %s", relaxed_D)
        logger.debug(f"Create contracted version")
        contracted_D = Contractor(ABCMeta.__new__(
            mcs, "_contracted_" + name, bases,
            {**dict, '__relaxed__': relaxed_D})).wrap()
        logger.debug(f"Contracted version created: %s", contracted_D)
        relaxed_D.__contracted__ = contracted_D

        return contracted_D


class Contractor:
    def __init__(self, cls):
        self._cls = cls

    def wrap(self):
        class_info = ClassContract.from_class(getattr(self._cls, '__relaxed__',
                                                      self._cls))
        logger.debug("..Wrap methods in contracted class")
        for name, method_info in class_info.method_info_by_name.items():
            logger.debug("...Wrap method %s in %s", name, self._cls.__name__)
            setattr(self._cls, name,
                    ContractedMethodFactory(class_info.invariants,
                                            method_info).create())
        return self._cls


class ContractedMethodFactory:
    def __init__(self, invariants: Sequence[Localized[OC]],
                 method_info: MethodInfo):
        self._invariants = invariants
        self._method_info = method_info

    def create(self) -> Callable:
        method = self._method_info.method

        def func(slf, *args, **kwargs):
            try:
                logger.info(
                    f"Contracted call %s.%s(%s, %s, %s)",
                    slf.__class__.__name__, self._method_info.name, slf, args,
                    kwargs)
                slf.__class__ = slf.__relaxed__
                old = deepcopy(slf)
                self.check_invariants(slf)
                self.check_requires(slf, *args, **kwargs)
                logger.debug(
                    f".Core call %s.%s",
                    slf.__class__.__name__, self._method_info.name)
                ret = method(slf, *args, **kwargs)
                self.check_ensures(slf, ret, old, *args, **kwargs)
                self.check_invariants(slf)
                slf.__class__ = slf.__contracted__
            except AssertionError as e:
                logger.exception("Assertion failed")
                raise
            return ret

        return func

    @staticmethod
    def check(method: OC, *args, **kwargs):
        if method is None:
            assert False
            return
        else:
            method(*args, **kwargs)

    def check_invariants(self, slf: Any):
        """
        Check the invariants of the `slf` class. All the invariants must be
        true.
        :param slf: the object
        """
        if not self._invariants:
            return

        logger.debug(f".Check invariants of %s: %s", slf, self._invariants)
        for invariant in reversed(self._invariants):
            try:
                ContractedMethodFactory.check(invariant.value, slf)
            except AssertionError as e:
                logger.error("..Invariant %s: NOT OK", invariant)
                raise
            else:
                logger.debug("..Invariant %s: ok", invariant)

    def check_requires(self, slf: Any, *args, **kwargs):
        """
        Check the pre-conditions

        :param slf:
        :param args:
        :param kwargs:
        :return:
        """
        if not self._method_info.requires:
            return

        logger.debug(".Check requires %s(%s, %s, %s)",
                     self._method_info.requires, slf, args, kwargs)
        for require in self._method_info.requires:
            try:
                ContractedMethodFactory.check(require.value, slf, *args,
                                              **kwargs)
            except AssertionError as e:
                error = e
                logger.error(f"..Require %s: NOT OK", require)
            else:
                logger.debug(f"..Require %s: ok", require)
                return

        raise error

    def check_ensures(self, slf: Any, ret: Any, old: Any, *args, **kwargs):
        if not self._method_info.ensures:
            return

        logger.debug(".Check ensures %s(%s, %s, %s, %s, %s)",
                     self._method_info.requires, slf, ret, old, args, kwargs)
        for ensure in reversed(self._method_info.ensures):
            try:
                ContractedMethodFactory.check(ensure.value, slf, ret, old,
                                              *args,
                                              **kwargs)
            except AssertionError as e:
                logger.error("..Ensure %s: NOT OK", ensure)
                raise
            else:
                logger.debug("..Ensure %s: ok", ensure)
