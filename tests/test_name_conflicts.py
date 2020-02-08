"""
These tests demonstrate an issue mentioned in
https://github.com/bobthemighty/punq/issues/28
"""

import pytest

import punq

from tests.conflicts import conflicting
from tests.conflicts import str_annotations
from tests.conflicts import type_annotations


@pytest.mark.parametrize("module", [str_annotations, type_annotations])
def test_no_conflict(module):
    container = punq.Container()
    container.register(conflicting.SameName)
    container.register(module.SameName)
    container.register(module.Consumer)
    assert container.resolve(module.Consumer).is_valid()


@pytest.mark.parametrize("module", [str_annotations, type_annotations])
def test_conflict(module):
    container = punq.Container()
    container.register(module.SameName)
    container.register(conflicting.SameName)
    container.register(module.Consumer)
    assert container.resolve(module.Consumer).is_valid()
