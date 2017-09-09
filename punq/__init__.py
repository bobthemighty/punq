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
        """Register a singleton instance to implement a service.

        Examples:
            If we have an object that is expensive to construct, or that
            wraps a resouce that must not be shared, we might choose to
            use a singleton instance.

            >>> class DataAccessLayer:
            ...     pass
            ...
            >>> class SqlAlchemyDataAccessLayer (DataAccessLayer):
            ...     def __init__(self, engine:SqlAlchemy.Engine):
            ...         pass
            ...
            >>> container.register(
            ...     DataAccessLayer,
            ...     SqlAlchemyDataAccessLayer(create_engine(db_uri)))"""
        self.__registrations[service].append(Registration(
            service,
            lambda: instance,
            {},
            {}))

    def register_concrete_service(self, service):
        """ Register a service as its own implementation.

            Examples:
                If we need to register a dependency, but we don't need to
                abstract it, we can register it as concrete.

                >>> class FileReader:
                ...     def read (self):
                ...         # Assorted legerdemain and rigmarole
                ...         pass
                ...
                >>> container.register(FileReader)"""

        if not type(service) is type:
            raise InvalidRegistrationException(
                    "The service %s can't be registered as its own implementation" %
                    (repr(service)))
        self.__registrations[service].append(Registration(
            service,
            service,
            self._get_needs_for_ctor(service),
            {}))

    def register(self, service, _factory=None, **kwargs):
        resolve_args = kwargs or {}
        if _factory is None:
            self.register_concrete_service(service)
        elif callable(_factory):
            self.register_service_and_impl(service, _factory, resolve_args)
        else:
            self.register_service_and_instance(service, _factory)

    def __getitem__(self, service):
        return self.__registrations[service]

    @property
    def registrations(self):
        return typing.MappingProxyType(self.__registrations)


class Container:

    def __init__(self):
        self.registrations = Registry()

    def register(self, service, _factory=None, **kwargs):
        self.registrations.register(service, _factory, **kwargs)

    def resolve_all(self, service, **kwargs):
        return [
            self._build_impl(x, kwargs) for x in self.registrations[service]
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

    def _get_generic_type_var(self, service):
        try:
            if service.__origin__ == typing.List:
                return service.__args__[0]
        except AttributeError as e:
            return None

    def resolve(self, service_key, **kwargs):
        impls = self.registrations[service_key]
        if len(impls) == 0:
            generic_list_service = self._get_generic_type_var(service_key)
            if generic_list_service is None:
                raise MissingDependencyException(
                        'Failed to resolve implementation for '+str(service_key))
            return self.resolve_all(generic_list_service)

        registration = impls[-1]
        return self._build_impl(registration, kwargs)
