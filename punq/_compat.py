import sys
import typing

GenericListClass = list
if sys.version_info >= (3, 11):
    ServiceKey = type
else:
    ServiceKey = typing.Type


def is_generic_list(service):
    try:
        return service.__origin__ == GenericListClass
    except AttributeError:
        return False


def ensure_forward_ref(self, service, factory, instance, **kwargs):
    if isinstance(service, str):
        self.register(typing.ForwardRef(service), factory, instance, **kwargs)
