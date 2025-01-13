import sys
import typing
import typing_extensions

GenericListClass = list
ServiceKey = typing_extensions.TypeForm


def is_generic_list(service):
    try:
        return service.__origin__ == GenericListClass
    except AttributeError:
        return False


def ensure_forward_ref(self, service, factory, instance, **kwargs):
    if isinstance(service, str):
        self.register(typing.ForwardRef(service), factory, instance, **kwargs)
