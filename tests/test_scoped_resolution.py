import pytest
from expects import be_a, expect

from punq import Container, MissingDependencyError
from tests.test_dependencies import (
    ConnectionStringFactory,
    FancyDbMessageWriter,
    MessageWriter,
    StdoutMessageWriter,
    TmpFileMessageWriter,
)


def test_scoped_service_with_no_dependencies():
    container = Container()
    container.register(MessageWriter, StdoutMessageWriter)

    child = container.child()
    expect(child.resolve(MessageWriter)).to(be_a(StdoutMessageWriter))


def test_when_overriding_a_service():
    """
    In this test, we replace the parent registration completely.
    The parent should resolve as normal, the child should return the overriden
    type.
    """
    parent = Container()
    parent.register(MessageWriter, StdoutMessageWriter)

    child = parent.child()
    child.register(MessageWriter, TmpFileMessageWriter, path="beep")

    expect(parent.resolve(MessageWriter)).to(be_a(StdoutMessageWriter))
    expect(child.resolve(MessageWriter)).to(be_a(TmpFileMessageWriter))


def test_when_a_child_adds_a_dependency():
    """
    In this test, we have a FancyDbMessageWriter in the parent and
    we add a ConnectionStringFactory to the child.
    In the parent context we should fail to resolve.
    In the child context we should succeed.
    """
    parent = Container()
    child = parent.child()

    parent.register(MessageWriter, FancyDbMessageWriter)
    child.register(ConnectionStringFactory, instance=lambda: "hello")

    with pytest.raises(MissingDependencyError):
        parent.resolve(MessageWriter)

    child.resolve(MessageWriter)


def test_when_the_parent_registers_a_dependency():
    """
    In this test, we have a FancyDbMessageWriter in the child and
    we add a ConnectionStringFactory to the parent.
    In the parent context we should fail to resolve.
    In the child context we should succeed.
    """
    parent = Container()
    child = parent.child()

    child.register(MessageWriter, FancyDbMessageWriter)
    parent.register(ConnectionStringFactory, instance=lambda: "hello")

    with pytest.raises(MissingDependencyError):
        parent.resolve(MessageWriter)

    child.resolve(MessageWriter)


def test_when_overriding_a_singleton_instance():
    """
    In this test, we have a FancyDbMessageWriter in the parent and
    we override a ConnectionStringFactory in the child.
    Both scopes should resolve, with different connection strings.
    """

    parent = Container()
    child = parent.child()

    parent.register(MessageWriter, FancyDbMessageWriter)
    parent.register(ConnectionStringFactory, instance=lambda: "hello")
    child.register(ConnectionStringFactory, instance=lambda: "world")

    assert parent.resolve(MessageWriter).connection_string == "hello"
    assert child.resolve(MessageWriter).connection_string == "world"


def test_when_inheriting_a_singleton_instance():
    """
    In this test, we have a FancyDbMessageWriter in the parent
    Both scopes should resolve, with the same connection string.
    """

    parent = Container()
    child = parent.child()

    parent.register(MessageWriter, FancyDbMessageWriter)
    parent.register(ConnectionStringFactory, instance=lambda: "hello")

    assert parent.resolve(MessageWriter).connection_string == "hello"
    assert child.resolve(MessageWriter).connection_string == "hello"


ContextBag = dict


class ThingDoer:
    def __init__(self, context: ContextBag):
        self.context = context


def test_when_registering_a_state_bag():
    parent = Container()
    parent.register(ThingDoer)

    first_child = parent.child()
    second_child = parent.child()

    first_child.register(ContextBag, instance={"msg": "hello"})
    second_child.register(ContextBag, instance={"msg": "world"})

    with pytest.raises(MissingDependencyError):
        parent.resolve(ThingDoer)

    assert first_child.resolve(ThingDoer).context["msg"] == "hello"
    assert second_child.resolve(ThingDoer).context["msg"] == "world"
