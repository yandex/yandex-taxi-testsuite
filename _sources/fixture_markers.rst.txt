Fixture markers
===============

``testsuite.fixture_markers`` lets plugins and tests attach typed metadata
to fixture functions and later collect the fixtures that carry a given
type and are visible to the current pytest request.

The helpers are framework-agnostic: they only depend on pytest fixture
definitions. userver uses them for service dependencies and static config
patches; other stacks can reuse the same marks for Postgres
initializers, mock setup, and similar discovery.

Marking a fixture
-----------------

Apply the mark to the original function, under ``@pytest.fixture``:

.. code-block:: python

   import dataclasses

   import pytest

   from testsuite import fixture_markers


   @dataclasses.dataclass(frozen=True)
   class PgInitializer:
       order: int


   def pg_init(*, order: int = 0):
       def decorator(function):
           return fixture_markers.mark(
               function,
               PgInitializer(order=order),
           )

       return decorator


   @pytest.fixture
   @pg_init()
   def init_users(pgsql):
       pgsql['mydb'].execute('INSERT INTO users ...')


   @pytest.fixture(name='init_orders')
   @pg_init(order=1)
   def _init_orders(pgsql):
       pgsql['mydb'].execute('INSERT INTO orders ...')

Querying marks
--------------

``get_infos(request, info_type)`` returns a ``dict`` of fixture name to
info for fixtures that:

* are visible to ``request`` (plugin, ancestor conftest, this module,
  this class);
* have a mark of ``info_type``;
* have a scope at least as wide as ``request.scope``.

.. code-block:: python

   initializers = fixture_markers.get_infos(request, PgInitializer)
   for name, _info in sorted(
       initializers.items(),
       key=lambda item: item[1].order,
   ):
       request.getfixturevalue(name)

Overriding a marked fixture
---------------------------

An override inherits the mark. ``get_infos`` looks at the definition
pytest would call. When that definition has no mark of the requested
type, the mark comes from the nearest overridden definition that has
one. A mark on the override replaces the inherited value. An override
cannot drop the mark.

.. code-block:: python

   # conftest.py

   @pytest.fixture
   @pg_init(order=1)
   def init_users(pgsql):
       pgsql['mydb'].execute('INSERT INTO users ...')

.. code-block:: python

   # test_users.py

   @pytest.fixture
   def init_users(init_users, pgsql):
       init_users
       pgsql['mydb'].execute('INSERT INTO guests ...')

   initializers = fixture_markers.get_infos(request, PgInitializer)
   # {'init_users': PgInitializer(order=1)}

.. automodule:: testsuite.fixture_markers
   :members: mark, get_infos
   :no-index:
