# https://github.com/bobthemighty/punq/issues/30
from contextvars import ContextVar

import punq

var: ContextVar[str] = ContextVar("var")


class DependsOnContextVar:
    def __init__(self, var: ContextVar[str]):
        self.var = var


def test_resolving_context_vars():
    container = punq.Container()
    container.register("var", instance=var)
    container.register(DependsOnContextVar)

    cls = container.resolve(DependsOnContextVar)
    assert cls
