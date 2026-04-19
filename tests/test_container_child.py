from punq import Container


class MyContainerSubclass(Container):
    """When retuning ``.child`` we need to preserve the container type."""


def test_container_child() -> None:
    child = MyContainerSubclass().child()
    assert isinstance(child, MyContainerSubclass)
