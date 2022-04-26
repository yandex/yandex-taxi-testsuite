from testsuite.plugins import testpoint


async def test_session(testpoint_checker_factory):
    session = testpoint.TestpointFixture(
        checker_factory=testpoint_checker_factory,
    )

    @session('foo')
    def point(data):
        pass

    assert session['foo'] is point
