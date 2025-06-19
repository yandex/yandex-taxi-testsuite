def test_history(testsuite_traceid_manager, _testsuite_traceid_history):
    assert testsuite_traceid_manager.trace_id in _testsuite_traceid_history
