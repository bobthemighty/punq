def is_generic_list(service):
    try:
        return service.__origin__ == list
    except AttributeError:
        return False
