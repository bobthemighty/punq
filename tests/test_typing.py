from typing import Callable, Generic, Type, TypeVar, Protocol, Union

# A flexible TypeVar for TService
TService = TypeVar("TService", bound=object)  # Must be an object type
TProtocol = TypeVar("TProtocol", bound=Protocol)

class _Registration(Generic[TService]):
    def __init__(
        self,
        service: Union[Type[TService], Protocol],  # Supports a class or a protocol
        builder: Callable[..., TService],  # Builder must return TService or compatible type
    ):
        self.service = service
        self.builder = builder

        # Runtime validation for classes (if service is a class)
        if isinstance(service, type):
            instance = builder()
            if not isinstance(instance, service):
                raise TypeError(f"Builder does not produce an instance of {service}")


class Parent(Protocol):
    def do_something(self) -> None:
        pass

class Child:
    def do_something(self) -> None:
        print("Child doing something")


f: Callable[..., Parent] = Child
