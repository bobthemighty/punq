"""Simple IOC container.

Classes:

    Container
    MissingDependencyError
    InvalidRegistrationError
    InvalidForwardReferenceError
    MissingDependencyException
    InvalidRegistrationException
    InvalidForwardReferenceException
    Scope

Misc Variables:

    empty
"""

import contextlib
import inspect
from collections import defaultdict
from enum import Enum
from importlib.metadata import PackageNotFoundError, version
from typing import Any, Callable, NamedTuple, get_type_hints

from ._compat import ensure_forward_ref, is_generic_list

with contextlib.suppress(PackageNotFoundError):
    __version__ = version(__name__)


class MissingDependencyException(Exception):
    """Deprecated alias for MissingDependencyError."""

    pass


class MissingDependencyError(MissingDependencyException):
    """Raised when a service, or one of its dependencies, is not registered.

    Examples:
        >>> import punq
        >>> container = punq.Container()
        >>> container.resolve("foo")
        Traceback (most recent call last):
        punq.MissingDependencyError: Failed to resolve implementation for foo
    """

    pass


class InvalidRegistrationException(Exception):
    """Deprecated alias for InvalidRegistrationError."""

    pass


class InvalidRegistrationError(InvalidRegistrationException):
    """Raised when a registration would result in an unresolvable service."""

    pass


class InvalidFactoryError(InvalidRegistrationError):
    def __init__(self, service, factory):
        super().__init__(f"Expected a callable factory for the service {service} but received {factory}")


class InvalidSelfRegistrationError(InvalidRegistrationError):
    def __init__(self, service):
        super().__init__(f"The service {service!r} can't be registered as its own implementation")


class InvalidForwardReferenceException(Exception):
    """Deprecated alias for InvalidForwardReferenceError."""

    pass


class InvalidForwardReferenceError(InvalidForwardReferenceException):
    """Raised when a registered service has a forward reference that can't be resolved.

    Examples:
        In this example, we register a service with a string as a type annotation.
        When we try to inspect the constructor for the service we fail with an
        InvalidForwardReferenceError

        >>> from dataclasses import dataclass
        >>> from punq import Container
        >>> @dataclass
        ... class Client:
        ...     dep: 'Dependency'
        >>> container = Container()
        >>> container.register(Client)
        Traceback (most recent call last):
        ...
        punq.InvalidForwardReferenceError: name 'Dependency' is not defined


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


class RegistrationScope:
    """
    Simple chained dictionary[service, list[implementation]].
    """

    def __init__(self, parent=None):
        self.parent = parent
        self.entries = defaultdict(list)

    def child(self):
        return RegistrationScope(self)

    def append(self, key, value):
        self.entries[key].append(value)

    def __get(self, key, result):
        if self.parent:
            self.parent.__get(key, result)
        for elem in self.entries[key]:
            result.append(elem)
        return result

    def get(self, key):
        return self.__get(key, [])


class Scope(Enum):
    """Controls the lifetime of resolved objects.

    Attributes:
        transient: create a fresh instance for each `resolve` call
        singleton: re-use a single instance for every `resolve` call
    """

    transient = 0
    singleton = 1


class _Registration(NamedTuple):
    service: str
    scope: Scope
    builder: Callable[[], Any]
    needs: Any
    args: list[Any]


class _Empty:
    pass


empty = _Empty()


def _match_defaults(spec):
    """Matches args with their defaults in the result of getfullargspec.

    inspect.getfullargspec returns a complex object that includes the defaults
    on args and kwonly args. This function takes a list of args, and a tuple of
    the last N defaults and returns a dict of args to defaults.

    These defaults are passed to _resolve_impl when building a needed dependency
    and used when a registration is missing.
    """
    ns = {}
    if spec.defaults is not None:
        # Defaults for args are just a tuple. We match args with their defaults
        # by position, starting at the first defaulted arg
        offset = len(spec.args) - len(spec.defaults)
        defaults = ([None] * offset) + list(spec.defaults)

        ns = {key: value for key, value in zip(spec.args, defaults) if value is not None}

    if spec.kwonlydefaults is not None:
        # defaults for kwargs are in a dict, so we just update the result dict.
        ns.update(spec.kwonlydefaults)

    return ns


class _Registry:
    def __init__(self, parent=None):
        if not parent:
            self.__registrations = RegistrationScope()
        else:
            self.__registrations = parent.__registrations.child()
        self._localns = {}

    def _get_needs_for_ctor(self, cls):
        try:
            return get_type_hints(cls.__init__, None, self._localns)
        except NameError as e:
            raise InvalidForwardReferenceError(str(e)) from e

    def register_service_and_impl(self, service, scope, impl, resolve_args):
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
        self.__registrations.append(
            service, _Registration(service, scope, impl, self._get_needs_for_ctor(impl), resolve_args)
        )

    def register_service_and_instance(self, service, instance):
        """Register a singleton instance to implement a service.

        Examples:
            If we have an object that is expensive to construct, or that
            wraps a resource that must not be shared, we might choose to
            use a singleton instance.

            >>> import sqlalchemy
            >>> from punq import Container
            >>> container = Container()

            >>> class DataAccessLayer:
            ...     pass
            ...
            >>> class SqlAlchemyDataAccessLayer(DataAccessLayer):
            ...     def __init__(self, engine: sqlalchemy.engine.Engine):
            ...         pass
            ...
            >>> container.register(
            ...     DataAccessLayer,
            ...     instance=SqlAlchemyDataAccessLayer(
            ...         sqlalchemy.create_engine("sqlite:///"))
            ... )
            <punq.Container object at 0x...>
        """
        self.__registrations.append(service, _Registration(service, Scope.singleton, lambda: instance, {}, {}))

    def register_concrete_service(self, service, scope, resolve_args=None):
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
        if not inspect.isclass(service):
            raise InvalidSelfRegistrationError(service)
        self.__registrations.append(
            service, _Registration(service, scope, service, self._get_needs_for_ctor(service), resolve_args or {})
        )

    def build_context(self, key, existing=None):
        if existing is None:
            return _ResolutionContext(key, self.__registrations.get(key))

        if key not in existing.targets:
            existing.targets[key] = _ResolutionTarget(key, self.__registrations.get(key))

        return existing

    def _update_localns(self, service):
        if isinstance(service, type):
            self._localns[service.__name__] = service
        else:
            self._localns[service] = service

    def register(self, service, factory=empty, instance=empty, scope=Scope.transient, **kwargs):
        resolve_args = kwargs or {}

        if instance is not empty:
            self.register_service_and_instance(service, instance)
        elif factory is empty:
            self.register_concrete_service(service, scope, resolve_args)
        elif callable(factory):
            self.register_service_and_impl(service, scope, factory, resolve_args)
        else:
            raise InvalidFactoryError(service, factory)

        self._update_localns(service)
        ensure_forward_ref(self, service, factory, instance, **kwargs)


class _ResolutionTarget:
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


class _ResolutionContext:
    def __init__(self, key, impls):
        self.targets = {key: _ResolutionTarget(key, impls)}
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
    """Provides dependency registration and resolution.

    This is the main entrypoint of the Punq library. In normal scenarios users
    will only need to interact with this class.
    """

    def __init__(self, registrations=None, auto_register=False):
        self.registrations = _Registry(registrations)
        self.register(Container, instance=self)
        self._singletons = {}
        self._auto_register = auto_register

    def register(self, service, factory=empty, instance=empty, scope=Scope.transient, **kwargs):
        """Register a dependency into the container.

        Each registration in Punq has a "service", which is the key used for
        resolving dependencies, and either an "instance" that implements the
        service or a "factory" that understands how to create an instance on
        demand.

        Examples:
            If we have an object that is expensive to construct, or that
            wraps a resouce that must not be shared, we might choose to
            use a singleton instance.

            >>> import sqlalchemy
            >>> from punq import Container
            >>> container = Container()

            >>> class DataAccessLayer:
            ...     pass
            ...
            >>> class SqlAlchemyDataAccessLayer(DataAccessLayer):
            ...     def __init__(self, engine: sqlalchemy.engine.Engine):
            ...         pass
            ...
            >>> dal = SqlAlchemyDataAccessLayer(sqlalchemy.create_engine("sqlite:///"))
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
        self.registrations.register(service, factory, instance, scope, **kwargs)
        return self

    def resolve_all(self, service, **kwargs):
        """Return all registrations for a given service.

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
            ...     def matches(self, req):
            ...         head = req.headers.get("Authorization", "")
            ...         return head.startswith("Basic ")
            ...
            >>> class TokenAuthenticator(Authenticator):
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

        return [self._build_impl(x, kwargs, context) for x in context.all_registrations(service)]

    def _build_impl(self, registration, resolution_args, context):
        """Instantiate the registered service."""
        spec = inspect.getfullargspec(registration.builder)
        target_args = spec.args + spec.kwonlyargs

        args = _match_defaults(spec)
        args.update({
            k: self._resolve_impl(v, resolution_args, context, args.get(k))
            for k, v in registration.needs.items()
            if k != "return" and k not in registration.args and k not in resolution_args
        })
        args.update(registration.args)

        if "self" in target_args:
            target_args.remove("self")
        condensed_resolution_args = {key: resolution_args[key] for key in resolution_args if key in target_args}
        args.update(condensed_resolution_args or {})

        result = registration.builder(**args)

        if registration.scope == Scope.singleton:
            self._singletons[registration.service] = result

        context[registration.service] = result

        return result

    def _should_auto_register(self, service_key, registration):
        if self._auto_register is False:
            return False
        return registration is None and inspect.isclass(service_key)

    def _resolve_impl(self, service_key, kwargs, context, default=None):
        context = self.registrations.build_context(service_key, context)

        if service_key in self._singletons:
            return self._singletons[service_key]

        if context.has_cached(service_key):
            return context[service_key]

        target = context.target(service_key)

        if target.is_generic_list():
            return self.resolve_all(target.generic_parameter)

        registration = target.next_impl()

        if registration is None and default is not None:
            return default

        if self._should_auto_register(service_key, registration):
            self.registrations.register_concrete_service(service_key, Scope.transient)
            return self._resolve_impl(service_key, kwargs, None, default)

        if registration is None:
            raise MissingDependencyError("Failed to resolve implementation for " + str(service_key))

        return self._build_impl(registration, kwargs, context)

    def resolve(self, service_key, **kwargs):
        """Build and return an instance of a registered service."""
        context = self.registrations.build_context(service_key)

        return self._resolve_impl(service_key, kwargs, context)

    def instantiate(self, service_key, **kwargs):
        """Instantiate an unregistered service."""
        registration = _Registration(
            service_key,
            Scope.transient,
            service_key,
            self.registrations._get_needs_for_ctor(service_key),
            {},
        )

        context = _ResolutionContext(service_key, [registration])

        return self._build_impl(registration, kwargs, context)

    def child(self):
        """Create a new container that inherits configuration from this one.

        You may need to change dependencies for a particular scope of your
        system, for example, to override them in tests, or to add per-request
        data.

        Punq supports "child" containers for this purpose.

        Examples:
            In this example, we want to register a per-request dependency into
            our child container. Each child will resolve its own instance of
            the RequestData.
            The order of registration is unimportant.

            >>> from collections import namedtuple

            >>> RequestData = namedtuple('RequestData', 'user_id is_admin')

            >>> class RequestHandler:
            ...
            ...     def __init__(self, state: RequestData):
            ...         self.state= state
            ...
            ...     def handle(self) -> None:
            ...         print(self.state)
            ...

            >>> app_container = Container()

            >>> first_request_container = app_container.child()
            >>> second_request_container = app_container.child()

            >>> first_request_container.register(RequestData, instance=RequestData(123, True))
            <punq.Container object at 0x...>

            >>> second_request_container.register(RequestData, instance=RequestData(789, False))
            <punq.Container object at 0x...>

            >>> app_container.register(RequestHandler)
            <punq.Container object at 0x...>

            >>> first_request_container.resolve(RequestHandler).handle()
            RequestData(user_id=123, is_admin=True)

            >>> second_request_container.resolve(RequestHandler).handle()
            RequestData(user_id=789, is_admin=False)
        """
        return Container(self.registrations, auto_register=self._auto_register)
