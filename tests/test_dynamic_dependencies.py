from punq import Container, Scope


class ConstructorDependency1:
    pass


class ConstructorDependency2:
    pass


class TraditionalClass:
    def __init__(
        self,
        dependency1: ConstructorDependency1,
        dependency2: ConstructorDependency2,
    ):
        self.dependency1 = dependency1
        self.dependency2 = dependency2


def test_can_resolve_dependencies_in_constructor_without_registration():
    container = Container()
    # container.register(ConstructorDependency1)
    # container.register(ConstructorDependency2)
    # ToDo: ^ The test will pass if we uncomment those or implement the feature.
    container.register(TraditionalClass)
    container.resolve(TraditionalClass)
