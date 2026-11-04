from expects import expect, have_len

from punq import Container
from tests.test_dependencies import MessageSpeaker, MessageWriter, StdoutMessageWriter, TmpFileMessageWriter


def test_can_resolve_a_list_of_dependencies():
    """
    In this test we create a composite MessageSpeaker that depends on a list of
    MessageWriters.

    When we resolve the speaker, it should be provided with a list of all the
    registered writers.
    """

    class BroadcastSpeaker:
        def __init__(self, writers: list[MessageWriter]) -> None:
            self.writers = writers

    container = Container()
    container.register(MessageWriter, StdoutMessageWriter)
    container.register(MessageWriter, TmpFileMessageWriter, path="my-file")
    container.register(MessageSpeaker, BroadcastSpeaker)

    instance = container.resolve(MessageSpeaker)

    expect(instance.writers).to(have_len(2))


def test_list_dependencies_receive_resolution_kwargs():
    class Writer:
        def __init__(self, path: str) -> None:
            self.path = path

    class OtherWriter(Writer):
        pass

    class Speaker:
        def __init__(self, writers: list[Writer]) -> None:
            self.writers = writers

    container = Container()
    container.register(Writer)
    container.register(Writer, OtherWriter)
    container.register(Speaker)

    direct = container.resolve_all(Writer, path="output.txt")
    assert [writer.path for writer in direct] == ["output.txt", "output.txt"]

    speaker = container.resolve(Speaker, path="output.txt")
    assert [type(writer) for writer in speaker.writers] == [Writer, OtherWriter]
    assert [writer.path for writer in speaker.writers] == ["output.txt", "output.txt"]


def test_list_resolution_keeps_runtime_service_keyword():
    class Writer:
        pass

    class Speaker:
        def __init__(self, service: str, writers: list[Writer]) -> None:
            self.service = service
            self.writers = writers

    container = Container()
    container.register(Writer)
    container.register(Speaker)

    speaker = container.resolve(Speaker, service="greeting")
    assert speaker.service == "greeting"
    assert len(speaker.writers) == 1
