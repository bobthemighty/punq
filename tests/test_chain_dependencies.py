from typing import Protocol

from expects import equal, expect

from punq import Container


class Filter(Protocol):
    def match(self, val) -> bool: ...


class Is_A(Filter):
    def __init__(self, successor: Filter, spy):
        self.spy = spy
        self.successor = successor

    def match(self, val):
        self.spy.append("is_a")

        return input == "A" or self.successor.match(input)


class Is_B(Filter):
    def __init__(self, successor: Filter, spy):
        self.spy = spy
        self.successor = successor

    def match(self, val):
        self.spy.append("is_b")

        return input == "B" or self.successor.match(input)


class Is_C(Filter):
    def __init__(self, successor: Filter, spy):
        self.spy = spy
        self.successor = successor

    def match(self, val):
        self.spy.append("is_c")

        return input == "C" or self.successor.match(input)


class NullFilter(Filter):
    def __init__(self, spy):
        self.spy = spy

    def match(self, val):
        self.spy.append("null")

        return False


def test_can_resolve_a_chain_of_dependencies():
    """
    In this test we construct a chain of responsibility
    that's managed by the container. When we invoke the chain
    each element of the chain is provided with its onward
    dependencies.
    """
    spy = []

    container = Container()
    container.register(Filter, NullFilter, spy=spy)
    container.register(Filter, Is_C, spy=spy)
    container.register(Filter, Is_B, spy=spy)
    container.register(Filter, Is_A, spy=spy)

    f = container.resolve(Filter)
    f.match("D")

    expect(spy).to(equal(["is_a", "is_b", "is_c", "null"]))
