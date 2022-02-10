from testsuite.plugins import testpoint


async def test_session():
    session = testpoint.TestpointFixture()

    @session('foo')
    def point(data):
        pass

    assert session['foo'] is point
