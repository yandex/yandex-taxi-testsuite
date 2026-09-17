Fixture markers
===============

``testsuite.fixture_markers`` lets plugins and tests attach typed metadata
to fixture functions and later collect the fixtures that carry a given
type and are visible to the current pytest request.

The helpers are framework-agnostic: they only depend on pytest fixture
definitions. Userver uses them for service dependencies and static config
patches; other stacks can reuse the same marks for SQL seeds, mock
setup, and similar discovery.

Marking a fixture
-----------------

Apply the mark to the original function, under ``@pytest.fixture``:

.. code-block:: python

   import dataclasses

   import pytest

   from testsuite import fixture_markers


   @dataclasses.dataclass(frozen=True)
   class SqlSeed:
       order: int


   def sql_seed(*, order: int = 0):
       def decorator(function):
           return fixture_markers.mark(function, SqlSeed(order=order))

       return decorator


   @pytest.fixture
   @sql_seed()
   def seed_users(pgsql):
       pgsql['mydb'].execute('INSERT INTO users ...')

Querying marks
--------------

``get_infos(request, info_type)`` returns a ``dict`` of fixture name to
info for fixtures that:

* are visible to ``request`` (plugin, ancestor conftest, this module,
  this class);
* have a mark of ``info_type``;
* have a scope at least as wide as ``request.scope``.

Overrides are not inherited: the winning fixture definition must carry
its own mark.

.. code-block:: python

   seeds = fixture_markers.get_infos(request, SqlSeed)
   for name, _info in sorted(
       seeds.items(),
       key=lambda item: item[1].order,
   ):
       request.getfixturevalue(name)

.. automodule:: testsuite.fixture_markers
   :members: mark, get_infos
   :no-index:
