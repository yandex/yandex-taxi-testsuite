import argparse
import itertools
import pathlib
import string
import subprocess
import typing

from testsuite.utils import subprocess_helper


MASTER_TPL_FILENAME = 'redis_master.conf.tpl'
SENTINEL_TPL_FILENAME = 'redis_sentinel.conf.tpl'
SLAVE_TPL_FILENAME = 'redis_slave.conf.tpl'
CLUSTER_TPL_FILENAME = 'redis_cluster.conf.tpl'

SENTINEL_PARAMS = [
    {
        'down_after_milliseconds': 60000,
        'failover_timeout': 180000,
        'parallel_syncs': 1,
    },
    {
        'down_after_milliseconds': 10000,
        'failover_timeout': 180000,
        'parallel_syncs': 5,
    },
]


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--output', type=pathlib.Path,
        help='Path to output directory',
    )
    parser.add_argument(
        '--host', type=int, default='localhost',
        help='An address to bind redis instances to',
    )
    parser.add_argument(
        '--master-port', type=int, nargs='+', default=[16379, 16389],
        help='Redis master port',
    )
    parser.add_argument(
        '--slave-port', type=int, nargs='+', default=[16380, 16381, 16390],
        help='Redis slave port',
    )
    parser.add_argument(
        '--sentinel-port', type=int, default=26379, help='Redis sentinel port',
    )
    parser.add_argument(
        '--cluster-mode', action='store_true', help='Run redis in cluster mode',
    )
    return parser.parse_args()


def _generate_redis_config(
        input_file: pathlib.Path,
        output_file: pathlib.Path,
        protected_mode_no: str,
        host: str,
        port: int,
        master_port: typing.Optional[int] = None,
) -> None:
    config_tpl = input_file.read_text()
    config_body = string.Template(config_tpl).substitute(
        protected_mode_no=protected_mode_no,
        host=host,
        port=port,
        master_port=master_port,
    )
    output_file.write_text(config_body)


def _generate_master(
        protected_mode_no: str,
        host: str,
        port: int,
        output_path: pathlib.Path,
        index: int,
) -> None:
    input_file = _redis_config_directory() / MASTER_TPL_FILENAME
    output_file = _construct_output_filename(
        output_path, MASTER_TPL_FILENAME, index,
    )
    _generate_redis_config(
        input_file, output_file, protected_mode_no, host, port,
    )


def _generate_slave(
        protected_mode_no: str,
        host: str,
        port: int,
        master_port: int,
        output_path: pathlib.Path,
        index: int,
) -> None:
    input_file = _redis_config_directory() / SLAVE_TPL_FILENAME
    output_file = _construct_output_filename(
        output_path, SLAVE_TPL_FILENAME, index,
    )
    _generate_redis_config(
        input_file, output_file, protected_mode_no, host, port, master_port,
    )


def _generate_sentinel(
        protected_mode_no: str,
        host: str,
        sentinel_port: int,
        ports: typing.List[int],
        output_path: pathlib.Path,
        params: typing.List,
) -> None:
    input_file = _redis_config_directory() / SENTINEL_TPL_FILENAME
    lines = ['daemonize yes', 'port %d' % sentinel_port, '']
    config_tpl = input_file.read_text()

    for index, (port, param) in enumerate(zip(ports, params)):
        config_body = string.Template(config_tpl).substitute(
            index=index,
            protected_mode_no=protected_mode_no,
            host=host,
            port=port,
            **param,
        )
        lines.append(config_body)

    output_path.joinpath('redis_sentinel.conf').write_text('\n'.join(lines))


def _generate_cluster_node(
        protected_mode_no: str,
        host: str,
        port: int,
        output_path: pathlib.Path,
) -> None:
    input_file = _redis_config_directory() / CLUSTER_TPL_FILENAME
    output_file = _construct_output_filename(
        output_path, CLUSTER_TPL_FILENAME, port,
    )
    _generate_redis_config(
        input_file, output_file, protected_mode_no, host, port,
    )


def _construct_output_filename(
        output_path: pathlib.Path, tpl_filename: str, number: int,
) -> pathlib.Path:
    name = tpl_filename.split('.', 1)[0]
    config_filename = ''.join((name, str(number), '.conf'))
    return output_path / config_filename


def _redis_config_directory() -> pathlib.Path:
    return pathlib.Path(__file__).parent / 'configs'


def redis_version() -> typing.List[int]:
    try:
        reply = subprocess_helper.sh('redis-server', '--version')
    except subprocess.CalledProcessError as err:
        raise RuntimeError(f'Subprocess error: {err}')

    start = 'Redis server '
    if not reply.startswith(start):
        raise RuntimeError(
            f'Can not parse redis server version from "{reply}"',
        )
    version_key = 'v'
    for token in reply[len(start) :].split(' '):
        key, value = token.split('=', 1)
        if key == version_key:
            return list(map(int, value.split('.')))
    raise RuntimeError(
        f'Tag "{version_key}" not found in redis server reply "{reply}"',
    )


def generate_redis_configs(
        output_path: pathlib.Path,
        host: str,
        master_ports: typing.List[int],
        slave_ports: typing.List[int],
        sentinel_port: int,
        cluster_mode: bool,
) -> None:
    protected_mode_no = ''
    if redis_version() >= [3, 2, 0]:
        protected_mode_no = 'protected-mode no'

    if cluster_mode:
        for port in itertools.chain(master_ports, slave_ports):
            _generate_cluster_node(protected_mode_no, host, port, output_path)

    else:
        for index, port in enumerate(master_ports):
            _generate_master(protected_mode_no, host, port, output_path, index)

        for index, port in enumerate(slave_ports):
            # every master gets two slaves
            _generate_slave(
                protected_mode_no, host, port, master_ports[index // 2], output_path, index,
            )

        _generate_sentinel(
            protected_mode_no, host, sentinel_port, master_ports, output_path, SENTINEL_PARAMS,
        )


def main():
    args = _parse_args()
    generate_redis_configs(
        output_path=args.output,
        host=args.host,
        master_ports=args.master_port,
        slave_ports=args.slave_port,
        sentinel_port=args.sentinel_port,
        cluster_mode=args.cluster_mode,
    )


if __name__ == '__main__':
    main()
