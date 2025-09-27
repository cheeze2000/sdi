from dataclasses import dataclass
from functools import wraps
from inspect import Signature, signature
from typing import Any, Callable, cast


@dataclass
class UnresolvedInjection:
    cls: type


class Injector:
    def __init__(self):
        self._callables: dict[type, Callable] = {}
        self._singletons: dict[type, Any] = {}

    def singleton(self, func):
        sig = signature(func)
        return_type = sig.return_annotation

        self._singletons[return_type] = None

        return self.transient(func)

    def transient(self, func):
        sig = signature(func)
        return_type = sig.return_annotation

        if return_type is Signature.empty:
            raise ValueError(
                f"Function '{func.__name__}' requires a return type annotation"
            )

        self._callables[return_type] = self._resolve_injections(func)

        return func

    def resolve(self, func):
        return self._resolve_injections(func)

    def _resolve_injections(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            sig = signature(func)
            for name, param in sig.parameters.items():
                if isinstance(param.default, UnresolvedInjection):
                    kwargs[name] = self._resolve_injection(param.default.cls)

            return func(*args, **kwargs)

        return wrapper

    def _resolve_injection[T](self, cls: type[T]) -> T:
        if cls not in self._callables:
            raise ValueError(f"No callables registered for type {cls}")

        if cls in self._singletons:
            if self._singletons[cls] is None:
                self._singletons[cls] = self._callables[cls]()
            return cast(T, self._singletons[cls])
        else:
            return cast(T, self._callables[cls]())

    def __call__[T](self, cls: type[T]) -> T:
        return cast(T, UnresolvedInjection(cls))


inject = Injector()
