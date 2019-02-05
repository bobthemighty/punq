from typing import List


def is_generic_list(service):
    try:
        return service.__origin__ == List
    except AttributeError:
        return False
