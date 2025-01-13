"""
Fundamentally, Punq stores a dict of lists, where the elements of the list are
the registered implementations for a service.

Originally, we used a defaultdict, which returned the empty list when a service
was unregistered.

In order to handle scoping, we need our own datastructure.
"""

from punq import RegistrationScope


def test_a_root_scope_returns_the_empty_list_when_nothing_is_registered():
    """
    If we have no registration for a key, then the implementations are an
    empty list.
    """
    scope = RegistrationScope()
    assert scope.get("some_key") == []


def test_a_scope_contains_items():
    """
    We can add items into a scope and get them back.
    Wow.
    """
    scope = RegistrationScope()
    scope.append("some-key", "hello")
    scope.append("some-key", "world")

    assert scope.get("some-key") == ["hello", "world"]


def test_a_child_scope_extends_its_parent():
    """
    When a child scope adds an item, it should be added to the list of
    the child's implementation, but not the parent's.
    """
    parent = RegistrationScope()
    child = parent.child()

    parent.append("some-key", "hello")
    child.append("some-key", "world")

    assert child.get("some-key") == ["hello", "world"]
    assert parent.get("some-key") == ["hello"]


def test_resolution_can_skip_a_level():
    """
    If someone goes nuts, the registrations should inherit across multiple
    levels intuitively.
    """

    grandparent = RegistrationScope()
    parent = RegistrationScope(grandparent)
    child = RegistrationScope(parent)

    grandparent.append("a", 1)
    grandparent.append("b", 2)
    parent.append("c", 3)
    child.append("b", "x")
    child.append("d", "x")

    assert grandparent.get("a") == [1]
    assert parent.get("a") == [1]
    assert child.get("a") == [1]

    assert grandparent.get("b") == [2]
    assert parent.get("b") == [2]
    assert child.get("b") == [2, "x"]

    assert grandparent.get("c") == []
    assert parent.get("c") == [3]
    assert child.get("c") == [3]

    assert grandparent.get("d") == []
    assert parent.get("d") == []
    assert child.get("d") == ["x"]
