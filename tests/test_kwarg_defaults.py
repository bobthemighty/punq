from expects import be, be_a, equal, expect, have_len
from punq import Container


class Dep:
    pass


class Client:
    def __init__(self, a: Dep, b: int = 10):
        self.a = a
        self.b = b


def test_can_create_instance_with_no_dependencies():
    container = Container()
    container.register(Dep)
    container.register(Client)
    expect(container.resolve(Client)).to(be_a(Client))
