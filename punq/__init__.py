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
import inspect
from collections import defaultdict
from enum import Enum
from typing import Annotated, Any, Generic, TypeVar, get_origin
from typing import Callable
from typing import get_type_hints
from typing import List
from typing import NamedTuple
from importlib.metadata import PackageNotFoundError, version
from typing_extensions import _AnnotatedAlias, get_args

from ._compat import ensure_forward_ref
from ._compat import is_generic_list

try:  # pragma no cover
    __version__ = version(__name__)
except PackageNotFoundError:  # pragma no cover
    # package is not installed
    pass


class MissingDependencyException(Exception):  # noqa
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


class InvalidRegistrationException(Exception):  # noqa
    """Deprecated alias for InvalidRegistrationError."""

    pass


class InvalidRegistrationError(InvalidRegistrationException):
    """Raised when a registration would result in an unresolvable service."""

    pass


class InvalidForwardReferenceException(Exception):  # noqa
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
    args: List[Any]


class _Empty:
    pass


empty = _Empty()


T = TypeVar("T")

class PunqAnnotation():
    pass

def _match_defaults(args, defaults):
    """Matches args with their defaults in the result of getfullargspec.

    inspect.getfullargspec returns a complex object that includes the defaults
    on args and kwonly args. This function takes a list of args, and a tuple of
    the last N defaults and returns a dict of args to defaults.
    """
    if defaults is None:
        return dict()

    offset = len(args) - len(defaults)
    defaults = ([None] * offset) + list(defaults)

    return {
        key: value
        for key, value in zip(args, defaults)  # noqa: B905
        if value is not None
    }


class _Registry:
    def __init__(self):
        self.__registrations = defaultdict(list)
        self._localns = dict()

    def _get_needs_for_ctor(self, cls):
        try:
            annotated_type_hints = get_type_hints(cls.__init__, None, self._localns, include_extras=True)
            non_annotated_type_hints = get_type_hints(cls.__init__, None, self._localns)

            type_hints = {}
            for kwarg_name, type_hint in annotated_type_hints.items():   
                if get_origin(type_hint) is Annotated and len(type_hint.__metadata__) > 0 and type_hint.__metadata__[0] == PunqAnnotation:
                   type_hints[kwarg_name] = type_hint
                else:
                   # if an annotation is not intended for  punq strip the annotation                  
                   type_hints[kwarg_name] = non_annotated_type_hints[kwarg_name]
            return type_hints
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
        self.__registrations[service].append(
            _Registration(
                service, scope, impl, self._get_needs_for_ctor(impl), resolve_args
            )
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
        self.__registrations[service].append(
            _Registration(service, Scope.singleton, lambda: instance, {}, {})
        )

    def register_concrete_service(self, service, scope):
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
            raise InvalidRegistrationError(
                "The service %s can't be registered as its own implementation"
                % (repr(service))
            )
        self.__registrations[service].append(
            _Registration(
                service, scope, service, self._get_needs_for_ctor(service), {}
            )
        )

    def build_context(self, key, existing=None):
        if existing is None:
            return _ResolutionContext(key, list(self.__getitem__(key)))

        if key not in existing.targets:
            existing.targets[key] = _ResolutionTarget(key, list(self.__getitem__(key)))

        return existing

    def _update_localns(self, service):
        if isinstance(service, type):
            self._localns[service.__name__] = service
        else:
            self._localns[service] = service

    def register(
        self, service, factory=empty, instance=empty, scope=Scope.transient, **kwargs
    ):
        resolve_args = kwargs or {}

        if instance is not empty:
            self.register_service_and_instance(service, instance)
        elif factory is empty:
            self.register_concrete_service(service, scope)
        elif callable(factory):
            self.register_service_and_impl(service, scope, factory, resolve_args)
        else:
            raise InvalidRegistrationError(
                f"Expected a callable factory for the service {service} but received {factory}"  # noqa
            )

        self._update_localns(service)
        ensure_forward_ref(self, service, factory, instance, **kwargs)

    def __getitem__(self, service):
        return self.__registrations[service]


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

    def __init__(self):
        self.registrations = _Registry()
        self.register(Container, instance=self)
        self._singletons = {}

    def register(
        self, service, factory=empty, instance=empty, scope=Scope.transient, **kwargs
    ):
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

        return [
            self._build_impl(x, kwargs, context)
            for x in context.all_registrations(service)
        ]

    def _build_impl(self, registration, resolution_args, context):
        """Instantiate the registered service."""
        spec = inspect.getfullargspec(registration.builder)
        target_args = spec.args

        args = _match_defaults(spec.args, spec.defaults)
        args.update(
            {
                k: self._resolve_impl(v, resolution_args, context, args.get(k))
                for k, v in registration.needs.items()
                if k != "return"
                and k not in registration.args
                and k not in resolution_args
            }
        )
        args.update(registration.args)

        if "self" in target_args:
            target_args.remove("self")
        condensed_resolution_args = {
            key: resolution_args[key] for key in resolution_args if key in target_args
        }
        args.update(condensed_resolution_args or {})

        result = registration.builder(**args)

        if registration.scope == Scope.singleton:
            self._singletons[registration.service] = result

        context[registration.service] = result

        return result

    def _resolve_impl(self, service_key, kwargs, context, default=None):

        context = self.registrations.build_context(service_key, context)

        if service_key in self._singletons:
            return self._singletons[service_key]

        if context.has_cached(service_key):
            return context[service_key]

        target = context.target(service_key)

        registration = target.next_impl()

        if registration is None and default is not None:
            return default

        if registration is None:
            raise MissingDependencyError(
                "Failed to resolve implementation for " + str(service_key)
            )

        if service_key in registration.needs.values():
            self._resolve_impl(service_key, kwargs, context)

        return self._build_impl(registration, kwargs, context)

    def resolve(self, service_key, **kwargs):
        """Build an return an instance of a registered service."""
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

        context = _ResolutionContext(service_key, list([registration]))

        return self._build_impl(registration, kwargs, context)
