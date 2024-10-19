from expects import equal, expect

from punq import Container


class Dep:
    pass


class Client:
    def __init__(self, a: Dep, b: int = 10):
        self.a = a
        self.b = b


def test_can_create_instance_with_defaulted_kwarg():
    container = Container()
    container.register(Dep)
    container.register(Client)

    client = container.resolve(Client)
    expect(client.b).to(equal(10))


def test_defaults_are_superseded_by_registrations():
    container = Container()
    container.register(Dep)
    container.register(Client)
    container.register(int, lambda: 3)

    client = container.resolve(Client)
    expect(client.b).to(equal(3))


def test_defaults_are_superseded_by_context():
    container = Container()
    container.register(Dep)
    container.register(Client)

    client = container.resolve(Client, b=5)
    expect(client.b).to(equal(5))
