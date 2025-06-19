from testsuite import tracing


def test_tracing():
    traceid_manager = tracing.TraceidManager(
        'this test', {'test0', 'test1', 'this test'}
    )

    assert traceid_manager.is_testsuite('this test')
    assert traceid_manager.is_testsuite('test0')
    assert traceid_manager.is_testsuite('test1')
    assert not traceid_manager.is_testsuite(None)
    assert not traceid_manager.is_testsuite('foo')

    assert traceid_manager.is_other_test('test0')
    assert traceid_manager.is_other_test('test1')
    assert not traceid_manager.is_other_test('this test')
    assert not traceid_manager.is_other_test(None)
    assert not traceid_manager.is_other_test('foo')
