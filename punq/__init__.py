from collections import defaultdict, namedtuple
import typing

class MissingDependencyException (Exception):
    pass


class InvalidRegistrationException (Exception):
    pass


Registration = namedtuple('Registration', ['service', 'builder', 'needs', 'args'])


class Registry:

    def __init__(self):
        self.__registrations = defaultdict(list)

    def _get_needs_for_ctor(self, cls):
        sig = typing.get_type_hints(cls.__init__)
        return sig

    def register_service_and_impl(self, service, impl, resolve_args):
        """Registers a concrete implementation of an abstract service.

           Examples:
                In this example, the EmailSender type is an abstract class
                and SmtpEmailSender is our concrete implementation.

                >>> class EmailSender:
                ...     def send(self, msg):
                ...         pass
                ...
                >>> class SmtpEmailSender (EmailSender):
                ...     def send(self, msg):
                ...         print("Sending message via smtp")
                ...
                >>> container.register(EmailSender, SmtpSender)
                >>> instance = container.resolve(EmailSender)
                >>> instance.send("Hello")
                >>> Sending message via smtp
        """
        self.__registrations[service].append(Registration(
            service,
            impl,
            self._get_needs_for_ctor(impl),
            resolve_args))

    def register_service_and_instance(self, service, instance):
        self.__registrations[service].append(Registration(
            service,
            lambda: instance,
            {},
            {}))

    def register_concrete_service(self, service):
        if not callable(service):
            raise InvalidRegistrationException(
                    "The service %s can't be registered as its own implementation" %
                    (repr(service)))
        self.__registrations[service].append(Registration(
            service,
            service,
            self._get_needs_for_ctor(service),
            {}))


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

    @property
    def registrations(self):
        return typing.MappingProxyType(self.__registrations)


class Container:

    def __init__(self):
        self.registrations = Registry()

    def register(self, service, factory=None, resolve_args=None):
        self.registrations.register(service, factory, resolve_args)

    def resolve_all(self, service):
        return [
            self.build_impl(x) for x in self.registrations[service]
        ]

    def _build_impl(self, registration, resolution_args=None):
        """Instantiate the registered service.
        """

        args = {
            k: self.resolve(v)
            for k, v in registration.needs.items()
            if k != 'return' and k not in registration.args

        }
        args.update(registration.args)
        args.update(resolution_args or {})

        return registration.builder(**args)

    def resolve(self, service_key, **kwargs):
        impls = self.registrations[service_key]
        if len(impls) == 0:
            raise MissingDependencyException()

        registration = impls[-1]
        return self.build_impl(registration, kwargs)
