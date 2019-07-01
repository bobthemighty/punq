from typing import Callable


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
        with open(self.path, "w") as f:
            f.write(msg)


ConnectionStringFactory = Callable[[], str]


class FancyDbMessageWriter(MessageWriter):
    def __init__(self, cstr: ConnectionStringFactory) -> None:
        self.connection_string = cstr()

    def write(self, msg):
        pass


class WrappingMessageWriter(MessageWriter):
    def __init__(self, wrapped: StdoutMessageWriter, context: str) -> None:
        self.wrapped = wrapped
        self.context = context

    def write(self, msg):
        self.wrapped.write(self.context + ": " + msg)


class HelloWorldSpeaker(MessageSpeaker):
    def __init__(self, writer: MessageWriter) -> None:
        self.writer = writer

    def speak(self):
        self.writer.write("Hello World")
