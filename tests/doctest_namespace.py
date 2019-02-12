import pytest


class SQLAlchemy(object):
    class Engine(object):
        """Emulates SQLAlchemy look-a-like in our examples."""


def create_engine(db_uri: str):
    """Creates fake engine."""
    return SQLAlchemy.Engine()


@pytest.fixture(autouse=True)
def setup_doctest_context(doctest_namespace):
    """Here we register all classes that we use in our doctest examples."""
    doctest_namespace["SQLAlchemy"] = SQLAlchemy
    doctest_namespace["create_engine"] = create_engine
