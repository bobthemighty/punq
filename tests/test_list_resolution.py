from typing import List

from expects import expect, have_len
from punq import Container
from tests.test_dependencies import (
    MessageSpeaker,
    MessageWriter,
    StdoutMessageWriter,
    TmpFileMessageWriter,
)


def test_can_resolve_a_list_of_dependencies():
    """
    In this test we create a composite MessageSpeaker that depends on a list of
    MessageWriters.

    When we resolve the speaker, it should be provided with a list of all the
    registered writers.
    """

    class BroadcastSpeaker:
        def __init__(self, writers: List[MessageWriter]) -> None:
            self.writers = writers

    container = Container()
    container.register(MessageWriter, StdoutMessageWriter)
    container.register(MessageWriter, TmpFileMessageWriter, path="my-file")
    container.register(MessageSpeaker, BroadcastSpeaker)

    instance = container.resolve(MessageSpeaker)

    expect(instance.writers).to(have_len(2))
