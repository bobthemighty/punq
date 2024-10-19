#!/usr/bin/env python3

import punq


class SomeVeryHeavyDep:
    pass


class SubSystemA:
    def __init__(self, d: SomeVeryHeavyDep):
        self.dep = d


class SubSystemB:
    def __init__(self, d: SomeVeryHeavyDep):
        self.dep = d


class Root:
    def __init__(self, a: SubSystemA, b: SubSystemB):
        self.a = a
        self.b = b


def test_that_repeated_resolutions_are_cached():
    """
    In this test we have two dependencies, each of which
    depends in turn on SomeVeryHeavyDep.

    We should use the same instance of SomeVeryHeavyDep
    for both resolutions, even though it is registered
    as transient.
    """
    container = punq.Container()

    container.register(SomeVeryHeavyDep, scope=punq.Scope.transient)
    container.register(SubSystemA)
    container.register(SubSystemB)
    container.register(Root)

    instance = container.resolve(Root)

    assert instance.a.dep is instance.b.dep
