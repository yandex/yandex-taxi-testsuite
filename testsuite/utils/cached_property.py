# pylint: disable=import-only-modules
# flake8: noqa
import sys

if sys.version_info > (3, 8):
    # pylint: disable=no-name-in-module
    from functools import cached_property
else:
    from cached_property import cached_property
