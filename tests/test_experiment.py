import pytest

from pipeline import Experiment


@pytest.fixture
def new_exp():
    return Experiment(conf=None, backend='tiny',
                      read_only=True)


#def test_empty_records(new_exp):
#    assert len(new_exp.records) == 0
