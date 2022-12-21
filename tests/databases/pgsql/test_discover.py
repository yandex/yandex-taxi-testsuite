import pytest

from testsuite.databases.pgsql import discover
from testsuite.databases.pgsql import exceptions


def test_database_name():
    assert discover._database_name(
        None, 'foo', discover.SINGLE_SHARD) == 'foo'
    assert discover._database_name(None, 'foo', 0) == 'foo_0'
    assert discover._database_name(None, 'foo', 1) == 'foo_1'
    assert discover._database_name(
        'foo', 'bar', discover.SINGLE_SHARD) == 'foo_bar'
    assert discover._database_name('foo', 'bar', 1) == 'foo_bar_1'
    assert discover._database_name(
        'yandex_taxi_eats_nomenclature_viewer', 'shards', 1) == (
            'ytenvs_c11de63930a0e27ca46d08_1'
    )
    assert discover._database_name(
        'yandex_taxi_eats_nomenclature_viewer',
        'shards', discover.SINGLE_SHARD) == (
            'ytenvs_c11de63930a0e27ca46d081b'
    )

    assert discover._database_name(
        None, 'ytenvc_cc21dd21265d91098dc39238', discover.SINGLE_SHARD) == (
            'ytenvc_cc21dd21265d91098dc39238'
    )
    with pytest.raises(exceptions.NameCannotBeShortend):
        assert discover._database_name(
            'yandex_taxi_eats_nomenclature_viewer',
            'conflict', discover.SINGLE_SHARD) == (
                'ytenvc_cc21dd21265d91098dc39238'
        )


def test_shortened():
    assert discover._shortened('foo_bar_maurice', '') == (
        'fbm_aaae77675222753dbe4d562a3e2'
    )
    assert discover._shortened('foo_bar_maurice', '_1') == (
        'fbm_aaae77675222753dbe4d562a3_1'
    )
    assert discover._shortened(
        'yandex_taxi_eats_nomenclature_viewer_shards', '_1'
    ) == (
        'ytenvs_c11de63930a0e27ca46d08_1'
    )

    assert discover._shortened('f_'* 22, '') == (
        'ffffffffffffffffffffff_8240e0c9'
    )
    assert discover._shortened('f_'* 30, '') == (
        'ffffffffffffffffffffffffffffff_'
    )
    with pytest.raises(exceptions.NameCannotBeShortend):
        discover._shortened('f_'* 32, '')
