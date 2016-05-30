from pipeline.lab.record import Record


def test_simple_attr_access():
    r = Record({})
    r['key'] = 'value'
    assert r.key == 'value'
