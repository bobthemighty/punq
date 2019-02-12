from typing import List, _ForwardRef


def is_generic_list(service):
    try:
        return service.__origin__ == List
    except AttributeError:
        return False


def ensure_forward_ref(self, service, factory, instance, **kwargs):
    if isinstance(service, str):
        self.register(_ForwardRef(service), factory, instance, **kwargs)
