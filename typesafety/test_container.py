from typing import Any

from typing_extensions import assert_type

from punq import Container, Scope

container = Container()


class Service: ...


class Impl: ...


# Registration
# ------------

assert_type(container.register(Service), Container)
assert_type(container.register(Service, Impl), Container)
assert_type(container.register(Service, Impl, scope=Scope.transient), Container)
assert_type(container.register(Service, Impl, scope=Scope.transient, extra=1), Container)
container.register("connection_str")  # type: ignore[call-overload]

assert_type(container.register("connection_str", instance=1), Container)
assert_type(container.register("connection_str", factory=Impl), Container)
assert_type(container.register("connection_str", Impl), Container)

container.register("connection_str", instance=1, scope=Scope.singleton)  # type: ignore[call-overload]


# Resolution
# ----------

assert_type(container.resolve(Service), Service)
assert_type(container.resolve("string"), Any)
assert_type(container.resolve(Impl, arg=1, other=2), Impl)


# Instantiate
# -----------

assert_type(container.instantiate(Service), Service)
assert_type(container.instantiate(Impl, args=None, kwargs=None), Impl)


# Child
# -----


class SubContainer(Container): ...


assert_type(container.child(), Container)
assert_type(SubContainer().child(), SubContainer)
