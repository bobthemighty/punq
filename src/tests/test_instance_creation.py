from expects import expect, be_a, equal, be
from punq import Container, MissingDependencyException, InvalidRegistrationException

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
                be_a(StdoutMessageWriter))


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
        self.writer = TmpFileMessageWriter('/tmp/my-file')
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



