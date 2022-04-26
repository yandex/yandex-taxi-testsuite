import pytest


class DisabledTestpointError(RuntimeError):
    pass


@pytest.fixture
def testpoint_checker_factory():
    def create_checker(name):
        def checker(op):
            if name == 'disabled':
                raise DisabledTestpointError

        return checker

    return create_checker


async def test_checker_success(testpoint):
    @testpoint('enabled')
    def enabled(data):
        pass

    assert not enabled.has_calls
    assert not enabled.times_called

    await enabled({})
    assert enabled.next_call()

    await enabled({})
    await enabled.wait_call()


async def test_checker_failure(testpoint):
    @testpoint('disabled')
    def disabled(data):
        pass

    with pytest.raises(DisabledTestpointError):
        assert not disabled.has_calls

    with pytest.raises(DisabledTestpointError):
        assert not disabled.times_called

    with pytest.raises(DisabledTestpointError):
        disabled.next_call()

    with pytest.raises(DisabledTestpointError):
        await disabled.wait_call()
