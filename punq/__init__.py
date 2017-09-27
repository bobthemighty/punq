import itertools
from collections import defaultdict, namedtuple
import typing
import logging


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

    def build_context(self, key, existing=None):
        if existing is None:
            return ResolutionContext(key, list(self.__getitem__(key)))
        if key not in existing.targets:
            existing.targets[key] = ResolutionTarget(key, list(self.__getitem__(key)))
        return existing

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


class ResolutionTarget:

    def __init__(self, key, impls):
        self.service = key
        self.impls = impls

    def is_generic_list(self):
        try:
            if self.service.__origin__ == typing.List:
                return self.service.__args__[0]
        except AttributeError as e:
            return None

    @property
    def generic_parameter(self):
        return self.service.__args__[0]

    def next_impl(self):
        if len(self.impls) > 0:
            return self.impls.pop()


class ResolutionContext:

    def __init__(self, key, impls):
        self.targets = {key: ResolutionTarget(key, impls)}
        self.cache = {}
        self.service = key

    def target(self, key):
        return self.targets.get(key)

    def has_cached(self, key):
        return key in self.cache

    def __getitem__(self, key):
        return self.cache.get(key)

    def __setitem__(self, key, instance):
        self.cache[key] = instance

    def all_registrations(self, service):
        return self.targets[service].impls


class Container:

    def __init__(self):
        self.registrations = Registry()

    def register(self, service, _factory=None, **kwargs):
        self.registrations.register(service, _factory, **kwargs)

    def resolve_all(self, service, **kwargs):
        context = self.registrations.build_context(service)
        return [
            self._build_impl(x, kwargs, context) for x in context.all_registrations(service)
        ]

    def _build_impl(self, registration, resolution_args, context):
        """Instantiate the registered service.
        """

        args = {
            k: self._resolve_impl(v, resolution_args, context)
            for k, v in registration.needs.items()
            if k != 'return' and k not in registration.args

        }
        args.update(registration.args)
        args.update(resolution_args or {})
        result = registration.builder(**args)
        context[registration.service] = result
        return result

    def _resolve_impl(self, service_key, kwargs, context):

        context = self.registrations.build_context(service_key, context)
        if context.has_cached(service_key):
            return context[service_key]

        target = context.target(service_key)
        if target.is_generic_list():
            return self.resolve_all(target.generic_parameter)

        registration = target.next_impl()
        if registration is None:
            raise MissingDependencyException(
                'Failed to resolve implementation for '+str(service_key))

        if service_key in registration.needs.values():
            self._resolve_impl(service_key, kwargs, context)
        return self._build_impl(registration, kwargs, context)


    def resolve(self, service_key, **kwargs):
        context = self.registrations.build_context(service_key)
        return self._resolve_impl(service_key, kwargs, context)
