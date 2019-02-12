import pytest


class SQLAlchemy(object):
    class Engine(object):
        """Emulates SQLAlchemy look-a-like in our examples."""


class Dependency(object):
    """Emulates a forward-ref dependency class in our examples."""


@pytest.fixture(autouse=True)
def setup_doctest_context(doctest_namespace):
    """Here we register all classes that we use in our doctest examples."""
    doctest_namespace['SQLAlchemy'] = SQLAlchemy
    doctest_namespace['Dependency'] = Dependency
