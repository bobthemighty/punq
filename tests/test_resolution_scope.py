"""
Fundamentally, Punq stores a dict of lists, where the elements of the list are
the registered implementations for a service.

Originally, we used a defaultdict, which returned the empty list when a service
was unregistered.

In order to handle scoping, we need our own datastructure.
"""
from collections import defaultdict
from punq import RegistrationScope

class RegistrationScope:

    def __init__(self, parent=None):
        self.parent = parent
        self.entries = defaultdict(list)

    def child(self):
        return RegistrationScope(self)

    def append(self, key, value):
        self.entries[key].append(value)

    def __get(self, key, result):
        if self.parent:
            self.parent.__get(key, result)
        for elem in self.entries[key]:
            result.append(elem)
        return result

    def get(self, key):
        return self.__get(key, [])


def test_a_root_scope_returns_the_empty_list_when_nothing_is_registered():
    scope = RegistrationScope()
    assert scope.get("some_key") == []

def test_a_scope_contains_items():
    scope = RegistrationScope()
    scope.append("some-key", "hello")
    scope.append("some-key", "world")

    assert scope.get("some-key") == ["hello", "world"]

def test_a_child_scope_extends_its_parent():
    parent = RegistrationScope()
    child = parent.child()

    parent.append("some-key", "hello")
    child.append("some-key","world")

    assert child.get("some-key") == ["hello", "world"]
    assert parent.get("some-key") == ["hello"]

def test_resolution_can_skip_a_level():

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

    assert grandparent.get("b") == [ 2 ]
    assert parent.get("b") == [ 2 ]
    assert child.get("b") == [2, "x"]

    assert grandparent.get("c") == []
    assert parent.get("c") == [ 3 ]
    assert child.get("c") == [ 3 ]

    assert grandparent.get("d") == []
    assert parent.get("d") == []
    assert child.get("d") == ["x"]
