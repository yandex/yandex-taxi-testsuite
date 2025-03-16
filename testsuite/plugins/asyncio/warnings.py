LOOP_DEPRECATION_MESSAGE = """\
Testsuite fixtures `event_loop` and `loop` are deprecated.

Tests and fixtures should use "asyncio.get_running_loop()" instead. Don't
forget to use async keyword when defining them."""
