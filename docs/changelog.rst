Changelog
---------

0.2.17
~~~~~~

- Add changelog
- matching: matching now is available as `testsuite.matching`
- matching: specify capture matching rule inside pattern

0.2.16
~~~~~~

- pytest-asyncio 0.25 support while keeping compatibility with 0.21.x

0.2.15
~~~~~~

- mongo: add mongo uri header
- kafka: implement message headers
- introduce traceback.hide

0.2.14
~~~~~~

- matching: add any_list, ListOf, any_dict, DictOf and Capture


0.2.13
~~~~~~

- kafka: wait until broker is stopped
- Update AUTHORS file

0.2.21
~~~~~~

- redis: wait for replicas and master negotiation in sentinel configuration
- redis: use CLUSTER NODES and CLUSTER SLOTS information to wait for cluster startup
- hide redundant tracebacks
