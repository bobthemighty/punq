from expects import expect, be_a, equal, be, have_len
from punq import Container, MissingDependencyException, InvalidRegistrationException
from typing import Callable, List, NewType


class MessageWriter:
    def write(self, msg: str) -> None:
        pass


class MessageSpeaker:
    def speak(self):
        pass


class StdoutMessageWriter(MessageWriter):
    def write(self, msg: str) -> None:
        print(msg)


class TmpFileMessageWriter(MessageWriter):
    def __init__(self, path):
        self.path = path

    def write(self, msg: str) -> None:
        with open(self.path) as f:
            f.write(msg)


ConnectionStringFactory = NewType("ConnectionStringFactory", Callable[[], str])


class FancyDbMessageWriter(MessageWriter):
    def __init__(self, cstr: ConnectionStringFactory) -> None:
        self.connection_string = cstr()

    def write(self, msg):
        pass


class HelloWorldSpeaker(MessageSpeaker):
    def __init__(self, writer: MessageWriter) -> None:
        self.writer = writer

    def speak(self):
        self.writer.write("Hello World")


class When_creating_instances_with_no_dependencies:
    def given_a_container(self):
        self.container = Container()
        self.container.register(MessageWriter, StdoutMessageWriter)

    def because_we_resolve_an_instance(self):
        self.result = self.container.resolve(MessageWriter)

    def it_should_be_an_instance_of_the_registered_implementor(self):
        expect(self.result).to(be_a(StdoutMessageWriter))


class When_creating_instances_with_dependencies:
    def given_a_container(self):
        self.container = Container()
        self.container.register(MessageWriter, StdoutMessageWriter)
        self.container.register(MessageSpeaker, HelloWorldSpeaker)

    def because_we_resolve_an_instance(self):
        self.result = self.container.resolve(MessageSpeaker)

    def it_should_be_an_instance_of_the_registered_implementor(self):
        expect(self.result).to(be_a(HelloWorldSpeaker))

    def it_should_have_injected_the_dependency(self):
        expect(self.result.writer).to(be_a(StdoutMessageWriter))


class When_a_dependency_is_missing:
    def given_a_container(self):
        self.container = Container()
        self.container.register(MessageSpeaker, HelloWorldSpeaker)

    def because_we_resolve_an_instance(self):
        try:
            self.instance = self.container.resolve(MessageSpeaker)
        except Exception as e:
            self.error = e

    def it_should_raise_an_exception(self):
        expect(self.error).to(be_a(MissingDependencyException))


class When_registering_a_service_with_no_implementor:
    def given_a_container(self):
        self.container = Container()

    def because_we_register_a_service_as_itself(self):
        self.container.register(StdoutMessageWriter)
        print(self.container.registrations)

    def it_should_register_as_its_own_implementor(self):
        expect(self.container.resolve(StdoutMessageWriter)).to(
            be_a(StdoutMessageWriter)
        )


class When_registering_a_service_with_a_custom_factory:
    def given_a_container(self):
        self.container = Container()

    def because_we_register_a_lambda_as_factory(self):
        self.container.register(MessageWriter, lambda: "Win")
        self.container.register(MessageSpeaker, HelloWorldSpeaker)

    def it_should_use_the_factory_to_resolve_the_service(self):
        expect(self.container.resolve(MessageSpeaker)).to(be_a(HelloWorldSpeaker))

    def it_should_have_resolved_the_dependency(self):
        expect(self.container.resolve(MessageSpeaker).writer).to(equal("Win"))


class When_registering_a_service_with_a_singleton_instance:
    def given_a_container_with_a_singleton_registration(self):
        self.container = Container()
        self.writer = TmpFileMessageWriter("/tmp/my-file")
        self.container.register(MessageWriter, self.writer)

    def because_we_resolve_the_instance(self):
        self.instance = self.container.resolve(MessageWriter)

    def it_should_return_the_singleton_instance(self):
        expect(self.instance).to(be(self.writer))


class When_registering_a_concrete_service_as_a_singleton:
    def given_a_container(self):
        self.container = Container()
        self.writer = StdoutMessageWriter()

    def because_we_register_the_service(self):
        try:
            self.container.register(self.writer)
        except Exception as e:
            self.error = e

    def it_should_have_raised_InvalidRegistrationException(self):
        expect(self.error).to(be_a(InvalidRegistrationException))


class When_registering_an_arbitrary_callable_as_a_concrete_implementation:
    """Concrete registrations need to take a callable type,
       not just a callable, otherwise we've no way to construct the service key"""

    def given_a_container(self):
        self.container = Container()

    def because_we_register_a_lambda_as_concrete(self):
        try:
            self.container.register(lambda: 5)
        except Exception as e:
            self.error = e

    def it_should_have_raised_InvalidRegistration(self):
        expect(self.error).to(be_a(InvalidRegistrationException))


class When_registering_the_same_service_multiple_times:
    def given_a_container(self):
        self.container = Container()

    def because_we_register_two_writers(self):
        self.container.register(MessageWriter, StdoutMessageWriter)
        self.container.register(MessageWriter, TmpFileMessageWriter("my-file"))

    def it_should_resolve_the_latest_registration(self):
        expect(self.container.resolve(MessageWriter)).to(be_a(TmpFileMessageWriter))

    def it_should_allow_me_to_resolve_all_implementations(self):
        expect(self.container.resolve_all(MessageWriter)).to(have_len(2))

    def it_should_return_the_implementations_in_registration_order(self):
        impls = self.container.resolve_all(MessageWriter)

        expect(impls[0]).to(be_a(StdoutMessageWriter))
        expect(impls[1]).to(be_a(TmpFileMessageWriter))


class When_registering_a_service_and_providing_an_argument:
    def given_a_container(self):
        self.container = Container()
        self.container.register(
            MessageWriter, FancyDbMessageWriter, cstr=lambda: "Hello world"
        )

    def because_we_resolve_an_instance(self):
        self.instance = self.container.resolve(MessageWriter)

    def it_should_build_the_instance(self):
        expect(self.instance).to(be_a(FancyDbMessageWriter))

    def it_should_have_passed_the_static_argument(self):
        expect(self.instance.connection_string).to(equal("Hello world"))


class When_we_provide_an_argument_at_resolution_time:
    def given_a_container(self):
        self.container = Container()
        self.container.register(MessageWriter, TmpFileMessageWriter)

    def because_we_resolve_with_an_argument(self):
        self.instance = self.container.resolve(MessageWriter, path="foo")

    def it_should_have_instantiated_the_instance_correctly(self):
        expect(self.instance.path).to(equal("foo"))


class When_we_need_to_resolve_a_list_of_dependencies:
    class BroadcastSpeaker:
        def __init__(self, writers: List[MessageWriter]) -> None:
            self.writers = writers

    def given_a_container(self):
        self.container = Container()
        self.container.register(MessageWriter, StdoutMessageWriter)
        self.container.register(MessageWriter, TmpFileMessageWriter, path="my-file")
        self.container.register(MessageSpeaker, self.BroadcastSpeaker)

    def because_we_depend_on_a_list_of_registered_dependencies(self):
        self.instance = self.container.resolve(MessageSpeaker)

    def it_should_inject_all_the_registered_dependencies(self):
        expect(self.instance.writers).to(have_len(2))


class Filter:
    pass


class Is_A(Filter):
    def __init__(self, next: Filter, spy):
        self.spy = spy
        self.next = next

    def match(self, input):
        self.spy.append("is_a")

        return input == "A" or self.next.match(input)


class Is_B(Filter):
    def __init__(self, next: Filter, spy):
        self.spy = spy
        self.next = next

    def match(self, input):
        self.spy.append("is_b")

        return input == "B" or self.next.match(input)


class Is_C(Filter):
    def __init__(self, next: Filter, spy):
        self.spy = spy
        self.next = next

    def match(self, input):
        self.spy.append("is_c")

        return input == "C" or self.next.match(input)


class NullFilter(Filter):
    def __init__(self, spy):
        self.spy = spy

    def match(self, input):
        self.spy.append("null")

        return False


class When_we_need_to_resolve_a_chain_of_collaborators:
    def given_a_container(self):
        self.spy = []
        self.container = Container()
        self.container.register(Filter, NullFilter, spy=self.spy)
        self.container.register(Filter, Is_C, spy=self.spy)
        self.container.register(Filter, Is_B, spy=self.spy)
        self.container.register(Filter, Is_A, spy=self.spy)

    def because_we_resolve_an_instance_of_the_chain(self):
        self.filter = self.container.resolve(Filter)
        self.filter.match("D")

    def it_should_call_each_element_in_turn(self):
        expect(self.spy).to(equal(["is_a", "is_b", "is_c", "null"]))
