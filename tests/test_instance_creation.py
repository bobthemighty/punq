from tempfile import NamedTemporaryFile

import pytest
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


def test_can_create_instance_with_no_dependencies():
    container = Container()
    container.register(MessageWriter, StdoutMessageWriter)
    expect(container.resolve(MessageWriter)).to(be_a(StdoutMessageWriter))


def test_dependencies_are_injected():
    container = Container()
    container.register(MessageWriter, StdoutMessageWriter)
    container.register(MessageSpeaker, HelloWorldSpeaker)

    speaker = container.resolve(MessageSpeaker)

    expect(speaker).to(be_a(HelloWorldSpeaker))
    expect(speaker.writer).to(be_a(StdoutMessageWriter))


def test_missing_dependencies_raise_exception():
    container = Container()
    container.register(MessageSpeaker, HelloWorldSpeaker)

    with pytest.raises(MissingDependencyError):
        container.resolve(MessageSpeaker)


def test_can_register_a_concrete_type():
    container = Container()
    container.register(StdoutMessageWriter)

    expect(container.resolve(StdoutMessageWriter)).to(be_a(StdoutMessageWriter))


def test_can_register_with_a_custom_factory():
    container = Container()
    container.register(MessageWriter, lambda: "win")
    container.register(MessageSpeaker, HelloWorldSpeaker)

    speaker = container.resolve(MessageSpeaker)

    expect(speaker).to(be_a(HelloWorldSpeaker))
    expect(speaker.writer).to(equal("win"))


def test_can_register_an_instance():
    container = Container()
    writer = TmpFileMessageWriter("my-file")
    container.register(MessageWriter, instance=writer)
    expect(container.resolve(MessageWriter)).to(equal(writer))


def test_resolves_instances():
    """
    No scope specified should work the way transient scope works
    """
    container = Container()
    container.register(MessageWriter, StdoutMessageWriter)

    mw1 = container.resolve(MessageWriter)
    mw2 = container.resolve(MessageWriter)
    expect(mw1).not_to(equal(mw2))


def test_resolves_instances_with_singleton_scope():
    container = Container()
    container.register(MessageWriter, StdoutMessageWriter, scope=Scope.singleton)

    mw1 = container.resolve(MessageWriter)
    mw2 = container.resolve(MessageWriter)
    expect(mw1).to(equal(mw2))


def test_resolves_instances_with_prototype_scope():
    container = Container()
    container.register(MessageWriter, StdoutMessageWriter, scope=Scope.transient)

    mw1 = container.resolve(MessageWriter)
    mw2 = container.resolve(MessageWriter)
    expect(mw1).not_to(equal(mw2))


def test_registering_an_instance_as_concrete_is_exception():
    """
    Concrete registrations need to be a constructable type
    or there's no key we can use for resolution.
    """
    container = Container()
    writer = MessageWriter()

    with pytest.raises(InvalidRegistrationError):
        container.register(writer)


def test_registering_an_instance_as_factory_is_exception():
    """
    Concrete registrations need to be a constructable type
    or there's no key we can use for resolution.
    """
    container = Container()
    writer = MessageWriter()

    with pytest.raises(InvalidRegistrationError):
        container.register(MessageWriter, writer)


def test_registering_a_callable_as_concrete_is_exception():
    """
    Likewise, if we register an arbitrary callable, there's
    no key by which we can later resolve, so we reject the
    registration
    """

    container = Container()

    with pytest.raises(InvalidRegistrationError):
        container.register(lambda: "oops")


def test_can_provide_arguments_to_registrations():
    container = Container()
    container.register(MessageWriter, FancyDbMessageWriter, cstr=lambda: "Hello world")

    writer = container.resolve(MessageWriter)

    expect(writer).to(be_a(FancyDbMessageWriter))
    expect(writer.connection_string).to(equal("Hello world"))


def test_can_provide_arguments_to_resolve():
    container = Container()
    container.register(MessageWriter, TmpFileMessageWriter)

    instance = container.resolve(MessageWriter, path="foo")
    expect(instance.path).to(equal("foo"))


def test_can_provide_arguments_to_resolve_having_dependencies():
    container = Container()
    container.register(StdoutMessageWriter, StdoutMessageWriter)
    container.register(MessageWriter, WrappingMessageWriter)

    instance = container.resolve(MessageWriter, context="bar")
    expect(instance.context).to(equal("bar"))


def test_can_provide_typed_arguments_to_resolve():
    container = Container()
    container.register(MessageWriter, TmpFileMessageWriter)
    container.register(TmpFileMessageWriter)
    container.register(HelloWorldSpeaker)

    tmpfile = NamedTemporaryFile()

    writer = container.resolve(MessageWriter, path=tmpfile.name)
    speaker = container.resolve(HelloWorldSpeaker, writer=writer)

    speaker.speak()

    tmpfile.seek(0)
    expect(tmpfile.read().decode()).to(equal("Hello World"))


def test_resolve_returns_the_latest_registration_for_a_service():
    container = Container()
    container.register(MessageWriter, StdoutMessageWriter)

    container.register(MessageWriter, TmpFileMessageWriter, path="my-file")

    expect(container.resolve(MessageWriter)).to(be_a(TmpFileMessageWriter))


def test_resolve_all_returns_all_registrations_in_order():
    container = Container()
    container.register(MessageWriter, StdoutMessageWriter)
    container.register(MessageWriter, TmpFileMessageWriter, path="my-file")

    [first, second] = container.resolve_all(MessageWriter)
    expect(first).to(be_a(StdoutMessageWriter))
    expect(second).to(be_a(TmpFileMessageWriter))


def test_can_instatiate_with_no_dependencies():
    container = Container()

    expect(container.instantiate(StdoutMessageWriter)).to(be_a(StdoutMessageWriter))


def test_instantiate_dependencies_are_injected():
    container = Container()
    container.register(MessageWriter, StdoutMessageWriter)
    container.register(MessageSpeaker)

    speaker = container.instantiate(HelloWorldSpeaker)

    expect(speaker).to(be_a(HelloWorldSpeaker))
    expect(speaker.writer).to(be_a(StdoutMessageWriter))


def test_can_instantiate_with_a_custom_factory():
    container = Container()
    container.register(MessageWriter, lambda: "win")
    container.register(MessageSpeaker)

    speaker = container.instantiate(HelloWorldSpeaker)

    expect(speaker).to(be_a(HelloWorldSpeaker))
    expect(speaker.writer).to(equal("win"))


def test_can_use_a_string_key():
    container = Container()
    container.register("foo", instance=1)
    assert container.resolve("foo") == 1
