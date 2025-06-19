Changelog
---------

0.3.6
~~~~~

- tracing: support custom trace_id generators (#192)

0.3.5
~~~~~

- fix pytest options in assertrepr plugin (#190)
- add datetime/timedelta matchers (#191)

0.3.4
~~~~~

- fix MacOS CI for kafka (#189)
- replace assertrepr plugin with experimental (#188)

0.3.3
~~~~~

- Add servicelogs plugin (#186)
- Add logcapture plugin (#184)
- Add asyncio_socket (#184)
- add ci tests to ensure, that userver testsuite tests works (#185)

0.3.2
~~~~~

- restore testsuite/annotations.py: userver depends on it (#183)

0.3.1
~~~~~

- Add experimental version of CompareTransform (#182)
- Specify tmp dir path inside tests (#181)
- split tests by core and databases (#180)

0.3.0
~~~~~
- remove unused imports from testsuite (#175)
- drop 3.7 and 3.8 support (#178)
- Drop legacy `loop` fixutre support (#177)
- Support external develop branch
- Fix assertrepr_compare_experimental mapping usage (#176)

0.2.21
~~~~~~

- asyncio legacy: close event loop (#173)
- Note valkey in docs (#172)
- Add Valkey support (#169)
- Revert "fix assertrepr_compare_experimental.py: replace pytest.Config with pytest.config.Config" (#170)

0.2.20
~~~~~~

- acallqueue: support callable instances (#166)
- fix assertrepr_compare_experimental.py: replace pytest.Config with pytest.config.Config (#167)

0.2.19
~~~~~~

- matching: full support for reprcompare (#165)
- add makefile tarets to run databases tests separetly and add split requirements (#162)
- Matching assertrepr (#163)
- New experimental assertrepr_compare plugin (#143)
- Depreacte event_loop and loop fixtures (#145)
- add testsuite.__version__ (#161)
- asyncio-legacy: do not close event loop (#160)
- ci: update outdated ubuntu runner (#158)

0.2.18
~~~~~~

- Remove loop fixture usage (#157)
- Add badges to README.rst (#154)
- Recursive partial dict (#150)
- deps: update packages versions (#153)
- acallqueue: add func property (#151)

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
