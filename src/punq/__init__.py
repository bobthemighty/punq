from collections import defaultdict, namedtuple
import typing

class MissingDependencyException (Exception):
    pass


class InvalidRegistrationException (Exception):
    pass


Registration = namedtuple('Registration', ['service', 'builder', 'args'])


class Registry:

    def __init__(self):
        self.__registrations = defaultdict(list)

    def register_service_and_impl(self, service, impl, resolve_args):
        self.__registrations[service].append((impl, resolve_args))

    def register_service_and_instance(self, service, instance):
        self.__registrations[service].append(((lambda: instance), {}))

    def register_concrete_service(self, service):
        if not callable(service):
            raise InvalidRegistrationException(
                    "The service %s can't be registered as its own implementation" %
                    (repr(service)))
        self.__registrations[service].append((service, {}))

    def register(self, service, factory=None, resolve_args=None):
        resolve_args = resolve_args or {}
        if factory is None:
            self.register_concrete_service(service)
        elif callable(factory):
            self.register_service_and_impl(service, factory, resolve_args)
        else:
            self.register_service_and_instance(service, factory)

    def __getitem__(self, service):
        return self.__registrations[service]


class Container:

    def __init__(self):
        self.registrations = Registry()

    def register(self, service, factory=None, resolve_args=None):
        self.registrations.register(service, factory, resolve_args)

    def resolve_all(self, service):
        return [
            self.build_impl(x, args) for x, args in self.registrations[service]
        ]

    def build_impl(self, factory, resolve_args):
        sig = typing.get_type_hints(factory.__init__)
        args = {
            k: self.resolve(v)
            for k, v in sig.items()
            if k != 'return' and k not in resolve_args

        }
        args.update(resolve_args)

        return factory(**args)

    def resolve(self, service_key):
        impls = self.registrations[service_key]
        if len(impls) == 0:
            raise MissingDependencyException()

        factory, args = impls[-1]
        return self.build_impl(factory, args)
