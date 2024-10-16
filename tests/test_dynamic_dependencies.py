from expects import equal, expect

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

def test_can_resolve_dependency_without_registration():
    container = Container()
    # container.register(ConstructorDependency1, scope=Scope.singleton)
    # container.register(ConstructorDependency2, scope=Scope.singleton)
    # ToDo: ^ The test will pass if we uncomment those or implement the feature.
    container.register(TraditionalClass)
    traditional_class = container.resolve(TraditionalClass)

    first_dependency = container.resolve(ConstructorDependency1)
    second_dependency = container.resolve(ConstructorDependency2)

    expect(traditional_class.dependency1).to(equal(first_dependency))
    expect(traditional_class.dependency2).to(equal(second_dependency))
