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

import logging
from abc import ABCMeta
from copy import deepcopy
from dataclasses import dataclass
from types import CodeType, FunctionType
from typing import (Callable, Sequence, Mapping, TypeVar, Generic, Optional,
                    Any, Iterable, List, Tuple, Dict)

_SPECIAL_METHOD_NAMES = {"__delitem__", "__setitem__",
                         "__iadd__", "__isub__", "__imul__",
                         "__imatmul__", "__itruediv__",
                         "__ifloordiv__", "__imod__", "__ipow__",
                         "__ilshift__", "__irshift__", "__iand__",
                         "__ixor__", "__ior__"}

# init the logger

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("Python Toy Contract")
logger.setLevel(logging.DEBUG)
logger.debug("Logger on.")

T = TypeVar('T')


@dataclass
class Localized(Generic[T]):
    """
    A value and its origin
    """
    value: T
    origin: type

    def __bool__(self):
        return bool(self.value)


@dataclass
class MethodContract:
    """
    The contract for a method: the method and its name, along with the
    related assertions.
    """
    name: str
    method: Callable
    requires: Sequence[Localized[Callable]]
    ensures: Sequence[Localized[Callable]]

    @staticmethod
    def from_methods(name: str, localized_methods: Sequence[Localized[Callable]]
                     ) -> "MethodContract":
        """
        Create a method contract from a hierarchy of localized_methods
        :param name: name of the method
        :param localized_methods: the localized_methods and their class of origin
        :return: the method contract
        """
        return _MethodContractFactory(name, localized_methods).create()


@dataclass
class ClassContract:
    """
    The contract for a class: the invariants and the contracts
     for each localized_methods.
    """
    invariants: Sequence[Localized[Callable]]
    method_info_by_name: Mapping[str, MethodContract]

    @staticmethod
    def from_class(cls: type) -> "ClassContract":
        """
        Create a class contract from a class
        :param cls: the class
        :return: the class contract
        """
        return _ClassContractFactory(cls).create()


class _ClassContractFactory:
    def __init__(self, cls: type):
        self._cls = cls

    def create(self) -> ClassContract:
        logger.debug(".Analyse class hierarchy of %s", self._cls)
        logger.debug("..Extract invariants %s", self._cls)
        invariants = _ClassContractFactory._find_invariants(self._cls)
        logger.debug("..Extract pre/post conditions %s", self._cls)
        method_info_by_name = self._find_method_info_by_name()
        return ClassContract(invariants, method_info_by_name)

    @staticmethod
    def _find_invariants(cls: type) -> Sequence[Localized[Callable]]:
        invariants = []
        for c in cls.__mro__[:-1]:
            invariant = _ClassContractFactory._get_attr_or_none(c,
                                                                "__invariant__")
            if invariant:
                logger.debug("...Found invariant in `%s`", c)
                invariants.append(
                    Localized(value=invariant,
                              origin=c))
        return invariants

    @staticmethod
    def _get_attr_or_none(c: type, attr: str) -> Optional[Any]:
        try:
            return c.__getattribute__(c, attr)
        except AttributeError:
            return None

    def _find_method_info_by_name(self) -> Mapping[str, MethodContract]:
        method_by_name = self._find_method_by_name()
        logger.debug("...Public localized_methods by name: %s", method_by_name)
        methods_by_name = _ClassContractFactory._find_methods_by_name(
            method_by_name, self._cls)
        logger.debug("...Sequence of localized_methods by name: %s",
                     methods_by_name)
        return {name: MethodContract.from_methods(name, methods_by_name[name])
                for name, method in method_by_name.items()}

    def _find_method_by_name(self) -> Mapping[str, Callable]:

        method_by_name = {}
        for method_name in self._public_methods():
            method_by_name[method_name] = getattr(self._cls, method_name)
        return method_by_name

    def _public_methods(self) -> Iterable[str]:
        for method_name in dir(self._cls):
            if ((not method_name.startswith("_")
                 or method_name in _SPECIAL_METHOD_NAMES)
                    and callable(getattr(self._cls, method_name))):
                yield method_name

    @staticmethod
    def _find_methods_by_name(method_by_name: Mapping[str, Callable], cls: type
                              ) -> Mapping[str, Sequence[Localized[Callable]]]:
        """"""
        methods_by_name = {}
        for name, method in method_by_name.items():
            self_method = Localized(value=method, origin=cls)
            parent_methods = _ClassContractFactory._find_parent_methods(cls,
                                                                        name)
            methods_by_name[name] = [self_method] + parent_methods
        return methods_by_name

    @staticmethod
    def _find_parent_methods(cls: type, name: str
                             ) -> List[Localized[Callable]]:
        """
        Find localized_methods of given name. The starting class is `cls`.
        Just follow the MRO, skipping the current class, until we find a class
        having the method. If there is no class, the parents localized_methods are an
        empty list. Else, we take the first method and append the parents
        localized_methods recusively
        :param cls: the class
        :param name: the name of the method
        :return:
        """
        localized_methods = (
            Localized(value=_ClassContractFactory._get_attr_or_none(c, name),
                      origin=c) for c in cls.__mro__[1:])
        localized_method = next((lm for lm in localized_methods if lm.value
                                 is not None), None)
        if localized_method is None:
            return []
        else:
            return [localized_method
                    ] + _ClassContractFactory._find_parent_methods(
                localized_method.origin, name)


class _MethodContractFactory:
    """
    A factory for MethodContract.
    """

    def __init__(self, name: str,
                 localized_methods: Sequence[Localized[Callable]]):
        """
        :param name: name of the method
        :param localized_methods: the hierarchy of localized_methods and their
        localizations.
        """
        self._name = name
        self._method = localized_methods[0].value
        self._localized_methods = localized_methods

    def create(self):
        """
        :return: a MethodContract
        """
        requires = self._extract_assertions("__require__", "__require_else__")
        ensures = self._extract_assertions("__ensure__", "__ensure_then__")
        return MethodContract(self._name, self._method, requires, ensures)

    def _extract_assertions(self, root_assertion_name: str,
                            children_assertion_name: str
                            ) -> Sequence[Localized[Callable]]:
        logger.debug(("...Extract assertions `%s` and `%s` "
                      "from localized_methods named `%s`"),
                     root_assertion_name, children_assertion_name, self._name)
        root_found = False
        localized_assertions = []
        for node in reversed(self._localized_methods):
            method = self._find_nested_assertion(node, root_assertion_name,
                                                 children_assertion_name,
                                                 root_found)
            if method:
                root_found = True
                localized_assertions.append(Localized(value=method,
                                                      origin=node.origin))
        return localized_assertions

    def _find_nested_assertion(self, node: Localized[Callable],
                               root_assertion_name: str,
                               children_assertion_name: str,
                               root_found) -> Optional[Callable]:
        function_by_name = self._find_nested_method_by_name(node.value)
        root_assertion_method = function_by_name.get(root_assertion_name, None)
        child_assertion_method = function_by_name.get(children_assertion_name,
                                                      None)
        assert not (root_assertion_method and child_assertion_method), (
            f"Use either {root_assertion_name} or "
            f"{children_assertion_name} in {node.origin}")
        assert not (root_found and root_assertion_method), (
            f"Use {children_assertion_name} instead of "
            f"{root_assertion_name} in {node.origin}")
        assert root_found or not child_assertion_method, (
            f"Missing {root_assertion_name} in {node.origin}")
        return root_assertion_method or child_assertion_method

    @staticmethod
    def _find_nested_method_by_name(method: Callable) -> Mapping[str, Callable]:
        consts = method.__code__.co_consts
        ret = {}
        for item in consts:
            if isinstance(item, CodeType):
                logger.debug("....Found nested function `%s` in `%s`",
                             item.co_name, method)
                ret[item.co_name] = FunctionType(item, globals())

        return ret


class ContractMeta(ABCMeta):
    """
    A metaclass for contracts.
    """

    def __new__(mcs: type, name: str, bases: Tuple[type], d: Dict[str, Any]):
        if not __debug__ or name == "Contract":
            return type.__new__(mcs, name, bases, d)
        logger.info(f"Create contracted/relaxed for class `{name}`")
        paranoid = d.get("__paranoid__", True)
        logger.debug("Create relaxed version")
        relaxed_bases = tuple([getattr(b, '__relaxed__', b) for b in bases])
        relaxed_class = ABCMeta.__new__(mcs, "relaxed_" + name, relaxed_bases,
                                        d)
        logger.debug("Relaxed version created: %s", relaxed_class)
        logger.debug("Create contracted version")
        contracted_class = _Contractor(ABCMeta.__new__(
            mcs, "_contracted_" + name, bases,
            {**d, '__relaxed__': relaxed_class}), paranoid).wrap()
        logger.debug("Contracted version created: %s", contracted_class)
        relaxed_class.__contracted__ = contracted_class

        return contracted_class


class Contract(metaclass=ContractMeta):
    """
    A class to inherit the ContractMeta class.
    """
    pass


class _Contractor:
    """
    A class to add contract check to a class.
    """

    def __init__(self, cls: type, paranoid: bool):
        """
        :param paranoid:
        :param cls: The class to process
        """
        self._paranoid = paranoid
        self._cls = cls

    def wrap(self) -> type:
        """
        :return:
        """
        class_info = ClassContract.from_class(getattr(self._cls, '__relaxed__',
                                                      self._cls))
        logger.debug("..Wrap localized_methods in contracted class")
        for name, method_info in class_info.method_info_by_name.items():
            logger.debug("...Wrap method %s in %s", name, self._cls.__name__)
            setattr(self._cls, name,
                    _ContractedMethodFactory(class_info.invariants,
                                             method_info,
                                             self._paranoid).create())

        def new_init(slf, *args, **kwargs):
            self._cls.__relaxed__.__init__(slf, *args, **kwargs)
            _ContractedMethodFactory(class_info.invariants, None,
                                     self._paranoid).check_invariants(slf)

        self._cls.__init__ = new_init

        return self._cls


class _ContractedMethodFactory:
    def __init__(self, invariants: Sequence[Localized[Callable]],
                 method_contract: MethodContract, paranoid: bool):
        """
        :param paranoid:
        :param invariants: the invariants
        :param method_contract: the contract of the method
        """
        self._invariants = invariants
        self._method_info = method_contract
        self._paranoid = paranoid

    def create(self) -> Callable:
        """
        :return: the method with checks
        """
        method = self._method_info.method

        def func(slf, *args, **kwargs):
            try:
                logger.info(
                    "Contracted call %s.%s(%s, %s, %s)",
                    slf.__class__.__name__, self._method_info.name, slf, args,
                    kwargs)
                slf.__class__ = slf.__relaxed__
                old = deepcopy(slf)
                if self._paranoid:
                    self.check_invariants(slf)
                self.check_requires(slf, *args, **kwargs)
                logger.debug(
                    ".Core call %s.%s",
                    slf.__class__.__name__, self._method_info.name)
                ret = method(slf, *args, **kwargs)
                self.check_ensures(slf, ret, old, *args, **kwargs)
                self.check_invariants(slf)
                slf.__class__ = slf.__contracted__
            except AssertionError:
                logger.exception("Assertion failed")
                raise
            return ret

        return func

    def check_invariants(self, slf: Any):
        """
        Check the invariants of the `slf` class. All the invariants must be
        true.
        :param slf: the object
        """
        if not self._invariants:
            return

        logger.debug(".Check invariants of %s: %s", slf, self._invariants)
        for invariant in reversed(self._invariants):
            try:
                invariant.value(slf)
            except AssertionError:
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
                require.value(slf, *args, **kwargs)
            except AssertionError as e:
                error = e
                logger.error("..Require %s: NOT OK", require)
            else:
                logger.debug("..Require %s: ok", require)
                return

        raise error

    def check_ensures(self, slf: Any, ret: Any, old: Any, *args, **kwargs):
        if not self._method_info.ensures:
            return

        logger.debug(".Check ensures %s(%s, %s, %s, %s, %s)",
                     self._method_info.requires, slf, ret, old, args, kwargs)
        for ensure in reversed(self._method_info.ensures):
            try:
                ensure.value(slf, ret, old, *args, **kwargs)
            except AssertionError:
                logger.error("..Ensure %s: NOT OK", ensure)
                raise
            else:
                logger.debug("..Ensure %s: ok", ensure)
