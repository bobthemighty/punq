import sys

if sys.version_info >= (3, 7, 0):
    from typing import ForwardRef

    GenericListClass = list
else:
    from typing import List, _ForwardRef as ForwardRef

    GenericListClass = List


def is_generic_list(service):
    try:
        return service.__origin__ == GenericListClass
    except AttributeError:
        return False


def ensure_forward_ref(self, service, factory, instance, **kwargs):
    if isinstance(service, str):
        self.register(ForwardRef(service), factory, instance, **kwargs)
