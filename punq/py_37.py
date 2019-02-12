from typing import ForwardRef


def is_generic_list(service):
    try:
        return service.__origin__ == list
    except AttributeError:
        return False


def ensure_forward_ref(self, service, factory, instance, **kwargs):
    if isinstance(service, str):
        self.register(ForwardRef(service), factory, instance, **kwargs)
