from testsuite import matching


def test_repr():
    assert (
        repr(matching.unordered_list([1, 2, 3])) == '<UnorderedList: [1, 2, 3]>'
    )


def test_unordered_list():
    assert [1, 3, 2] == matching.unordered_list([3, 2, 1])
    assert [{'v': 'a'}, {'v': 'b'}] == matching.unordered_list(
        [{'v': 'b'}, {'v': 'a'}], key=lambda x: x['v']
    )
    assert 123 != matching.unordered_list([])


def test_visit():
    pred = matching.unordered_list([1, 2, 3])

    visited = []

    def visitor(value):
        visited.append(value)
        return value

    copy = pred.__testsuite_visit__(visitor)

    assert visited == [[1, 2, 3]]
    assert copy == pred
    assert copy is not pred
