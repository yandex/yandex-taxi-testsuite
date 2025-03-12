def test_regular_collection_is_accessible(mongodb):
    assert 'foo' in mongodb.get_aliases()


def test_extra_collection_is_not_accessible(mongodb):
    # because we did not override mongo_schema_extra_directories fixture
    assert 'foo_extra' not in mongodb.get_aliases()
