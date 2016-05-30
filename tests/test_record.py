import pytest

from pipeline.lab.record import Record


@pytest.fixture
def rec():
    return Record({'key1': 'value1'})


def test_simple_attr_access(rec):
    assert rec.key1 == 'value1'


def test_simple_setitem(rec):
    rec['key2'] = 'value2'
    assert rec.key2 == 'value2'


def test_is_not_dirty_when_unchanged(rec):
    assert not rec._is_dirty


def test_is_dirty_when_changed(rec):
    rec['key2'] = 'value2'
    assert rec._is_dirty
