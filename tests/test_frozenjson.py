import pytest

from pipeline.lab.FrozenJSON import FrozenJSON


@pytest.fixture
def simple():
    return FrozenJSON({'key1': 'value1'})


@pytest.fixture
def nested():
    return FrozenJSON({'key1': {'subkey1': 'value1'}})


def test_simple_attr(simple):
    assert simple.key1 == 'value1'


def test_simple_nested(nested):
    assert nested.key1.subkey1 == 'value1'


def test_nested_returns_frozen(nested):
    assert isinstance(nested.key1, FrozenJSON)
