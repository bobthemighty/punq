"""
As per github.com/bobthemighty/punq/issues/9 if we register a type in the
container that uses a forward declaration for a dependency, we hit a bug in
the `typing` module that causes a name error.

The fix is to provide a dict of the previously registered services to the
get_type_hints function, so that we can resolve forward references to any
previously registered service.
"""

import attr

import punq
import pytest


@attr.s(auto_attribs=True)
class Client:
    dep: "Dependency"


@attr.s(auto_attribs=True)
class Dependency:
    val = 1


class DataAccessLayer:
    val = 2


def test_can_resolve_objects_with_forward_references():
    """
    If we've already registered a type with the name 'Dependency' then we
    should be able to resolve the forward reference.
    """
    container = punq.Container()
    container.register(Dependency)
    container.register(Client)

    instance = container.resolve(Client)
    assert instance.dep.val == 1


def test_forward_references_must_be_registered_before_their_clients():
    """
    If we haven't registered the 'Dependency' type yet, then we'll raise
    a specific error so people can at least work out what the hell is happening
    """
    container = punq.Container()

    with pytest.raises(punq.InvalidForwardReferenceException):
        container.register(Client)


def test_forward_references_can_be_registered_as_strings():
    """
    For cases where you want to declare a ref like 'module.Dep' we allow you to
    resolve a forward reference with an arbitrary string.
    """
    container = punq.Container()
    container.register("Dependency", DataAccessLayer)
    container.register(Client)

    instance = container.resolve(Client)
    assert instance.dep.val == 2
