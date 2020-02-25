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


def ensure_forward_ref(self, service, frame, factory, instance, **kwargs):
    if isinstance(service, str):
        self.register(ForwardRef(service), frame, factory, instance, **kwargs)


def get_globals_and_locals_of_parent(maybe_frame):
    try:
        parent_frame = maybe_frame.f_back
    except AttributeError:
        return {}, {}
    return parent_frame.f_globals, parent_frame.f_locals
