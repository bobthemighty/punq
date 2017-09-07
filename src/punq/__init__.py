import typing

class MissingDependencyException (Exception):
    pass


class InvalidRegistrationException (Exception):
    pass


class Container:

    def __init__(self):
        self.registrations = {}

    def register_service_and_impl(self, service, impl):
        self.registrations[service] = impl

    def register_service_and_instance(self, service, instance):
        self.registrations[service] = lambda: instance

    def register_concrete_service(self, service):
        if not callable(service):
            raise InvalidRegistrationException(
                    "The service %s can't be registered as its own implementation" %
                    (repr(service)))
        self.registrations[service] = service

    def register(self, service, factory=None):
        if factory is None:
            self.register_concrete_service(service)
        elif callable(factory):
            self.register_service_and_impl(service, factory)
        else:
            self.register_service_and_instance(service, factory)

    def resolve(self, service_key, context=None):
        factory = self.registrations.get(service_key)
        if factory is None:
            raise MissingDependencyException()

        sig = typing.get_type_hints(factory.__init__)
        args = {
            k: self.resolve(v, context)
            for k, v in sig.items() if k != 'return'
        }

        return factory(**args)
