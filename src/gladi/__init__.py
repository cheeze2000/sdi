from dataclasses import dataclass
from enum import StrEnum
from functools import wraps
from inspect import Signature, signature
from typing import Any, Callable, cast


class InjectionKind(StrEnum):
    Singleton = "singleton"
    Scoped = "scoped"
    Transient = "transient"


@dataclass
class UnresolvedInjection:
    cls: type


class Injector:
    def __init__(self):
        self._registry: dict[type, InjectionKind] = {}
        self._callables: dict[type, Callable] = {}
        self._instances: dict[type, Any] = {}

        self._is_in_scope: bool = False

    def singleton(self, func):
        self._register_injectable(func, InjectionKind.Singleton)

    def scoped(self, func):
        self._register_injectable(func, InjectionKind.Scoped)

    def transient(self, func):
        self._register_injectable(func, InjectionKind.Transient)

    def resolve(self, func):
        return self._resolve_injections(func)

    def _register_injectable(self, func: Callable, kind: InjectionKind) -> None:
        sig = signature(func)
        return_type = sig.return_annotation

        if return_type is Signature.empty:
            raise ValueError(
                f"Function '{func.__name__}' requires a return type annotation"
            )

        self._registry[return_type] = kind
        self._callables[return_type] = self._resolve_injections(func)

    def _resolve_injections(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            is_original_scope = not self._is_in_scope
            self._is_in_scope = True

            sig = signature(func)
            for name, param in sig.parameters.items():
                if isinstance(param.default, UnresolvedInjection):
                    kwargs[name] = self._resolve_injection(param.default.cls)

            return_value = func(*args, **kwargs)

            if is_original_scope:
                self._instances = {
                    cls: instance
                    for cls, instance in self._instances.items()
                    if self._registry[cls] == InjectionKind.Singleton
                }

                self._is_in_scope = False

            return return_value

        return wrapper

    def _resolve_injection[T](self, cls: type[T]) -> T:
        if cls not in self._registry:
            raise ValueError(f"Type {cls} is not registered as an injectable")

        kind = self._registry[cls]

        if kind == InjectionKind.Transient:
            return cast(T, self._callables[cls]())
        elif cls not in self._instances:
            self._instances[cls] = self._callables[cls]()

        return cast(T, self._instances[cls])

    def __call__[T](self, cls: type[T]) -> T:
        return cast(T, UnresolvedInjection(cls))


inject = Injector()
