#!/usr/bin/env python3

from expects import expect, be_a

from punq import Container

class Dependency:
    pass

class Initializable:

    def __init__(self, dep: Dependency):
        self.dep = dep

def test_when_requesting_an_initialisable_object_that_is_not_in_the_container():
    container = Container()
    expect(container.resolve(Initializable)).to(be_a(Initializable))
