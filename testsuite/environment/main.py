import argparse
import contextlib
import importlib
import logging
import subprocess
import sys

from testsuite.logging import logger

from . import control
from . import utils

DEFAULT_SERVICE_PLUGINS = [
    'testsuite.databases.mongo.pytest_plugin',
    'testsuite.databases.pgsql.pytest_plugin',
    'testsuite.databases.redis.pytest_plugin',
]


def main(service_plugins=None):
    utils.ensure_non_root_user()
    if service_plugins is None:
        service_plugins = DEFAULT_SERVICE_PLUGINS
    testsuite_services = _register_services(service_plugins)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--build-dir', help='Build directory path', required=True,
    )
    parser.add_argument(
        '--services',
        nargs='+',
        help='List of services (default: %(default)s)',
        default=sorted(testsuite_services.keys()),
    )
    parser.add_argument(
        '--log-level',
        choices=['debug', 'info', 'warning', 'error', 'critical'],
        default='debug',
    )
    parser.set_defaults(handler=None)

    subparsers = parser.add_subparsers()

    command_parser = subparsers.add_parser('start', help='Start services')
    command_parser.set_defaults(handler=_command_start)

    command_parser = subparsers.add_parser('stop', help='Stop services')
    command_parser.set_defaults(handler=_command_stop)

    command_parser = subparsers.add_parser(
        'run', help='Run command with services started',
    )
    command_parser.add_argument('command', nargs='+', help='Command to run')
    command_parser.set_defaults(handler=_command_run)

    args = parser.parse_args()

    if args.handler is None:
        parser.error('No command given')

    _setup_logging(args.log_level.upper())

    env = control.TestsuiteEnvironment(
        worker_id='master',
        build_dir=args.build_dir,
        reuse_services=False,
        verbose=2,
    )
    for service_name, service_class in testsuite_services.items():
        env.register_service(service_name, service_class)
    args.handler(env, args)


def _setup_logging(log_level):
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logger.ColoredLevelFormatter(colors_enabled=sys.stderr.isatty()),
    )
    root_logger.addHandler(handler)


def _command_start(env, args):
    for service_name in args.services:
        env.ensure_started(service_name)


def _command_stop(env, args):
    for service_name in args.services:
        env.stop_service(service_name)


def _command_run(env, args):
    _command_start(env, args)
    with contextlib.closing(env):
        exit_code = subprocess.call(args.command)
        sys.exit(exit_code)


def _register_services(service_plugins):
    services = {}

    def _register_service(name, factory=None):
        def decorator(factory):
            services[name] = factory

        if factory is None:
            return decorator
        return decorator(factory)

    for modname in service_plugins:
        mod = importlib.import_module(modname)
        mod.pytest_service_register(register_service=_register_service)
    return services


if __name__ == '__main__':
    main()
