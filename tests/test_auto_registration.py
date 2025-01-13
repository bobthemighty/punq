#!/usr/bin/env python3

import typing

import pytest
from expects import be_a, expect

from punq import Container


class Dependency:
    pass


class Initializable:
    def __init__(self, dep: Dependency):
        self.dep = dep


class NotInitializable(typing.Protocol):
    def do_thing(self): ...


def test_when_requesting_an_initialisable_object_that_is_not_in_the_container():
    container = Container(auto_register=True)
    expect(container.resolve(Initializable)).to(be_a(Initializable))


def test_when_requesting_an_uninitialisable_object_that_is_not_in_the_container():
    container = Container(auto_register=True)
    with pytest.raises(TypeError):
        container.resolve(NotInitializable)
