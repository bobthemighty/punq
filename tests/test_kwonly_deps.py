from typing import Protocol

import punq


class Parser(Protocol):
    def parse(self, val: str) -> str: ...


class Writer(Protocol):
    def write(self, val: str) -> None: ...


class Doer:
    def __init__(self, *, p: Parser, w: Writer, name: str = "Barry"):
        self.parser = p
        self.writer = w
        self.name = name

    def do(self, val: str):
        self.writer.write(f"{self.name}: {self.parser.parse(val)}")


class ListWriter:
    def __init__(self, target: list):
        self.output = target

    def write(self, val) -> None:
        self.output.append(val)


class ReverseParser:
    def parse(self, val) -> str:
        return val[::-1]


class IdentityParser:
    def parse(self, val) -> str:
        return val


def test_can_resolve_with_kwonlyargs():
    container = punq.Container()
    result = []
    container.register(Parser, ReverseParser)
    container.register(Writer, instance=ListWriter(result))
    container.register(Doer)

    doer = container.resolve(Doer)
    doer.do("hello world")

    otherdoer = container.resolve(Doer, name="Tom")
    otherdoer.do("dlrow olleh")

    assert result == ["Barry: dlrow olleh", "Tom: hello world"]


def test_can_register_with_kwonlyargs():
    container = punq.Container()
    result = []
    container.register(Parser, ReverseParser)
    container.register(Writer, instance=ListWriter(result))
    container.register(Doer, name="Frodo")

    doer = container.resolve(Doer)
    doer.do("hello world")

    otherdoer = container.resolve(Doer, name="Bilbo", p=IdentityParser())
    otherdoer.do("hello world")

    assert result == ["Frodo: dlrow olleh", "Bilbo: hello world"]
