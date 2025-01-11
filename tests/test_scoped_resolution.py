from expects import be_a, equal, expect

from punq import Container, InvalidRegistrationError, MissingDependencyError, Scope
from tests.test_dependencies import (
    FancyDbMessageWriter,
    HelloWorldSpeaker,
    MessageSpeaker,
    MessageWriter,
    StdoutMessageWriter,
    TmpFileMessageWriter,
    WrappingMessageWriter,
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
