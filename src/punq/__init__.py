from collections import defaultdict
import typing

class MissingDependencyException (Exception):
    pass


class InvalidRegistrationException (Exception):
    pass


class Container:

    def __init__(self):
        self.registrations = defaultdict(list)

    def register_service_and_impl(self, service, impl):
        self.registrations[service].append(impl)

    def register_service_and_instance(self, service, instance):
        self.registrations[service].append(lambda: instance)

    def register_concrete_service(self, service):
        if not callable(service):
            raise InvalidRegistrationException(
                    "The service %s can't be registered as its own implementation" %
                    (repr(service)))
        self.registrations[service].append(service)

    def register(self, service, factory=None):
        if factory is None:
            self.register_concrete_service(service)
        elif callable(factory):
            self.register_service_and_impl(service, factory)
        else:
            self.register_service_and_instance(service, factory)


    def resolve_all(self, service):
        return [
            self.build_impl(x) for x in self.registrations[service]
        ]

    def build_impl(self, factory):
        sig = typing.get_type_hints(factory.__init__)
        args = {
            k: self.resolve(v)
            for k, v in sig.items() if k != 'return'
        }

        return factory(**args)

    def resolve(self, service_key):
        impls = self.registrations[service_key]
        if len(impls) == 0:
            raise MissingDependencyException()

        factory = impls[-1]
        return self.build_impl(factory)
