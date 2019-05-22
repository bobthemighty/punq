import typing
from collections import defaultdict, namedtuple

from pkg_resources import DistributionNotFound, get_distribution

from ._compat import is_generic_list, ensure_forward_ref

try:  # pragma no cover
    __version__ = get_distribution(__name__).version
except DistributionNotFound:  # pragma no cover
    # package is not installed
    pass


class MissingDependencyException(Exception):
    """
    Raised when a service, or one of its dependencies, is not registered.

    Examples:
        >>> import punq
        >>> container = punq.Container()
        >>> container.resolve("foo")
        Traceback (most recent call last):
        punq.MissingDependencyException: Failed to resolve implementation for foo
    """

    pass


class InvalidRegistrationException(Exception):
    """
    Raised when a registration would result in an unresolvable service.
    """

    pass


class InvalidForwardReferenceException(Exception):
    """
    Raised when a registered service has a forward reference that can't be
    resolved.

    Examples:
        In this example, we register a service with a string as a type annotation.
        When we try to inspect the constructor for the service we fail with an
        InvalidForwardReferenceException

        >>> from attr import dataclass
        >>> from punq import Container
        >>> @dataclass
        ... class Client:
        ...     dep: 'Dependency'
        >>> container = Container()
        >>> container.register(Client)
        Traceback (most recent call last):
        ...
        punq.InvalidForwardReferenceException: name 'Dependency' is not defined


        This error can be resolved by first registering a type with the name
        'Dependency' in the container.

        >>> class Dependency:
        ...     pass
        ...
        >>> container.register(Dependency)
        <punq.Container object at 0x...>
        >>> container.register(Client)
        <punq.Container object at 0x...>
        >>> container.resolve(Client)
        Client(dep=<punq.Dependency object at 0x...>)


        Alternatively, we can register a type using the literal key 'Dependency'.

        >>> class AlternativeDependency:
        ...     pass
        ...
        >>> container = Container()
        >>> container.register('Dependency', AlternativeDependency)
        <punq.Container object at 0x...>
        >>> container.register(Client)
        <punq.Container object at 0x...>
        >>> container.resolve(Client)
        Client(dep=<punq.AlternativeDependency object at 0x...>)

    """

    pass


Registration = namedtuple("Registration", ["service", "builder", "needs", "args"])


class Empty:
    pass


empty = Empty()


class Registry:
    def __init__(self):
        self.__registrations = defaultdict(list)
        self._localns = dict()

    def _get_needs_for_ctor(self, cls):
        try:
            return typing.get_type_hints(cls.__init__, None, self._localns)
        except NameError as e:
            raise InvalidForwardReferenceException(str(e))

    def register_service_and_impl(self, service, impl, resolve_args):
        """Registers a concrete implementation of an abstract service.

           Examples:
                In this example, the EmailSender type is an abstract class
                and SmtpEmailSender is our concrete implementation.

                >>> from punq import Container
                >>> container = Container()

                >>> class EmailSender:
                ...     def send(self, msg):
                ...         pass
                ...
                >>> class SmtpEmailSender(EmailSender):
                ...     def send(self, msg):
                ...         print("Sending message via smtp: " + msg)
                ...
                >>> container.register(EmailSender, SmtpEmailSender)
                <punq.Container object at 0x...>
                >>> instance = container.resolve(EmailSender)
                >>> instance.send("Hello")
                Sending message via smtp: Hello
        """
        self.__registrations[service].append(
            Registration(service, impl, self._get_needs_for_ctor(impl), resolve_args)
        )

    def register_service_and_instance(self, service, instance):
        """Register a singleton instance to implement a service.

        Examples:
            If we have an object that is expensive to construct, or that
            wraps a resource that must not be shared, we might choose to
            use a singleton instance.

            >>> from punq import Container
            >>> container = Container()

            >>> class DataAccessLayer:
            ...     pass
            ...
            >>> class SqlAlchemyDataAccessLayer(DataAccessLayer):
            ...     def __init__(self, engine: SQLAlchemy.Engine):
            ...         pass
            ...
            >>> container.register(
            ...     DataAccessLayer,
            ...     instance=SqlAlchemyDataAccessLayer(create_engine("sqlite:///"))
            ... )
            <punq.Container object at 0x...>
        """
        self.__registrations[service].append(
            Registration(service, lambda: instance, {}, {})
        )

    def register_concrete_service(self, service):
        """Register a service as its own implementation.

            Examples:
                If we need to register a dependency, but we don't need to
                abstract it, we can register it as concrete.

                >>> from punq import Container
                >>> container = Container()
                >>> class FileReader:
                ...     def read(self):
                ...         # Assorted legerdemain and rigmarole
                ...         pass
                ...
                >>> container.register(FileReader)
                <punq.Container object at 0x...>
        """
        if not type(service) is type:
            raise InvalidRegistrationException(
                "The service %s can't be registered as its own implementation"
                % (repr(service))
            )
        self.__registrations[service].append(
            Registration(service, service, self._get_needs_for_ctor(service), {})
        )

    def build_context(self, key, existing=None):
        if existing is None:
            return ResolutionContext(key, list(self.__getitem__(key)))

        if key not in existing.targets:
            existing.targets[key] = ResolutionTarget(key, list(self.__getitem__(key)))

        return existing

    def _update_localns(self, service):
        if type(service) == type:
            self._localns[service.__name__] = service
        else:
            self._localns[service] = service

    def register(self, service, factory=empty, instance=empty, **kwargs):
        resolve_args = kwargs or {}

        if instance is not empty:
            self.register_service_and_instance(service, instance)
        elif factory is empty:
            self.register_concrete_service(service)
        elif callable(factory):
            self.register_service_and_impl(service, factory, resolve_args)
        else:
            raise InvalidRegistrationException(
                f"Expected a callable factory for the service {service} but received {factory}"
            )
        self._update_localns(service)
        ensure_forward_ref(self, service, factory, instance, **kwargs)

    def __getitem__(self, service):
        return self.__registrations[service]


class ResolutionTarget:
    def __init__(self, key, impls):
        self.service = key
        self.impls = impls

    def is_generic_list(self):
        return is_generic_list(self.service)

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
    """
    Provides dependency registration and resolution.

    This is the main entrypoint of the Punq library. In normal scenarios users
    will only need to interact with this class.
    """

    def __init__(self):
        self.registrations = Registry()

    def register(self, service, factory=empty, instance=empty, **kwargs):
        """
        Register a dependency into the container.

        Each registration in Punq has a "service", which is the key used for
        resolving dependencies, and either an "instance" that implements the
        service or a "factory" that understands how to create an instance on
        demand.

        Examples:
            If we have an object that is expensive to construct, or that
            wraps a resouce that must not be shared, we might choose to
            use a singleton instance.

            >>> from punq import Container
            >>> container = Container()

            >>> class DataAccessLayer:
            ...     pass
            ...
            >>> class SqlAlchemyDataAccessLayer(DataAccessLayer):
            ...     def __init__(self, engine: SQLAlchemy.Engine):
            ...         pass
            ...
            >>> dal = SqlAlchemyDataAccessLayer(create_engine("sqlite:///"))
            >>> container.register(
            ...     DataAccessLayer,
            ...     instance=dal
            ... )
            <punq.Container object at 0x...>
            >>> assert container.resolve(DataAccessLayer) is dal

            If we need to register a dependency, but we don't need to
                abstract it, we can register it as concrete.

            >>> class FileReader:
            ...     def read (self):
            ...         # Assorted legerdemain and rigmarole
            ...         pass
            ...
            >>> container.register(FileReader)
            <punq.Container object at 0x...>
            >>> assert type(container.resolve(FileReader)) == FileReader

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
            >>> container.register(EmailSender, SmtpEmailSender)
            <punq.Container object at 0x...>
            >>> instance = container.resolve(EmailSender)
            >>> instance.send("beep")
            Sending message via smtp
        """

        self.registrations.register(service, factory, instance, **kwargs)
        return self

    def resolve_all(self, service, **kwargs):
        """
        Return all registrations for a given service.

        Some patterns require us to use multiple implementations of an
        interface at the same time.

        Examples:

            In this example, we want to use multiple Authenticator instances to
            check a request.

            >>> class Authenticator:
            ...     def matches(self, req):
            ...         return False
            ...
            ...     def authenticate(self, req):
            ...         return False
            ...
            >>> class BasicAuthenticator(Authenticator):
            ...
            ...     def matches(self, req):
            ...         head = req.headers.get("Authorization", "")
            ...         return head.startswith("Basic ")
            ...
            >>> class TokenAuthenticator(Authenticator):
            ...
            ...     def matches(self, req):
            ...         head = req.headers.get("Authorization", "")
            ...         return head.startswith("Bearer ")
            ...
            >>> def authenticate_request(container, req):
            ...     for authn in req.resolve_all(Authenticator):
            ...         if authn.matches(req):
            ...             return authn.authenticate(req)
        """
        context = self.registrations.build_context(service)

        return [
            self._build_impl(x, kwargs, context)
            for x in context.all_registrations(service)
        ]

    def _build_impl(self, registration, resolution_args, context):
        """Instantiate the registered service.
        """

        args = {
            k: self._resolve_impl(v, resolution_args, context)
            for k, v in registration.needs.items()
            if k != "return" and k not in registration.args and k not in resolution_args
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
                "Failed to resolve implementation for " + str(service_key)
            )

        if service_key in registration.needs.values():
            self._resolve_impl(service_key, kwargs, context)

        return self._build_impl(registration, kwargs, context)

    def resolve(self, service_key, **kwargs):
        context = self.registrations.build_context(service_key)

        return self._resolve_impl(service_key, kwargs, context)
