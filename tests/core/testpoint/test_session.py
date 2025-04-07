async def test_session(testpoint):
    @testpoint('foo')
    def point(data):
        pass

    assert testpoint['foo'] is point


async def test_mapping(testpoint):
    assert not testpoint

    @testpoint('foo')
    def tp_foo():
        pass

    @testpoint('bar')
    def tp_bar():
        pass

    assert testpoint['foo'] is tp_foo
    assert testpoint['bar'] is tp_bar
    assert sorted(testpoint) == ['bar', 'foo']
    assert testpoint
    assert len(testpoint) == 2
    assert 'foo' in testpoint
    assert 'foo2' not in testpoint
