import argparse
import os
import string


MASTER_TPL_FILENAME = 'redis_master.conf.tpl'
SENTINEL_TPL_FILENAME = 'redis_sentinel.conf.tpl'
SLAVE_TPL_FILENAME = 'redis_slave.conf.tpl'

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
    parser.add_argument('--output', help='Path to output directory')
    parser.add_argument(
        '--host',
        type=int,
        default='localhost',
        help='Redis host for sentinel config',
    )
    parser.add_argument(
        '--master0-port', type=int, default=16379, help='Redis masters0 port',
    )
    parser.add_argument(
        '--master1-port', type=int, default=16389, help='Redis masters0 port',
    )
    parser.add_argument(
        '--slave0-ports', type=int, default=16380, help='Redis slave0 port',
    )
    parser.add_argument(
        '--slave1-ports', type=int, default=16390, help='Redis slave1 port',
    )
    parser.add_argument(
        '--slave2-ports', type=int, default=16381, help='Redis slave2 port',
    )
    parser.add_argument(
        '--sentinel-port', type=int, default=26379, help='Redis sentinel port',
    )
    return parser.parse_args()


def _generate_redis_config(
        input_file, output_file, host, port, master_port=None,
):
    with open(input_file, 'r') as fconfig:
        config_tpl = fconfig.read()
        config_body = string.Template(config_tpl).substitute(
            host=host, port=port, master_port=master_port,
        )

    with open(output_file, 'w') as fconfig:
        fconfig.write(config_body)


def _generate_master(host, port, output_path, index):
    input_file = os.path.join(_redis_config_directory(), MASTER_TPL_FILENAME)
    output_file = _construct_output_filename(
        output_path, MASTER_TPL_FILENAME, index,
    )
    _generate_redis_config(input_file, output_file, host, port)


def _generate_slave(host, port, master_port, output_path, index):
    input_file = os.path.join(_redis_config_directory(), SLAVE_TPL_FILENAME)
    output_file = _construct_output_filename(
        output_path, SLAVE_TPL_FILENAME, index,
    )
    _generate_redis_config(input_file, output_file, host, port, master_port)


def _generate_sentinel(host, sentinel_port, ports, output_path, params):
    input_file = os.path.join(_redis_config_directory(), SENTINEL_TPL_FILENAME)
    lines = ['daemonize yes', 'port %d' % sentinel_port, '']
    with open(input_file, 'r') as fconfig:
        config_tpl = fconfig.read()

    for index, (port, param) in enumerate(zip(ports, params)):
        config_body = string.Template(config_tpl).substitute(
            index=index, host=host, port=port, **param,
        )
        lines.append(config_body)

    output_file = os.path.join(output_path, 'redis_sentinel.conf')
    with open(output_file, 'w') as fconfig:
        fconfig.write('\n'.join(lines))


def _construct_output_filename(output_path, tpl_filename, number):
    config_filename, _ = os.path.splitext(tpl_filename)
    name, exp = os.path.splitext(config_filename)
    config_filename = ''.join((name, str(number), exp))
    return os.path.join(output_path, config_filename)


def _redis_config_directory():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'configs'))


def generate_redis_configs(
        output_path,
        host,
        master0_port,
        master1_port,
        slave0_port,
        slave1_port,
        slave2_port,
        sentinel_port,
):
    _generate_master(host, master0_port, output_path, 0)
    _generate_master(host, master1_port, output_path, 1)

    _generate_slave(host, slave0_port, master0_port, output_path, 0)
    _generate_slave(host, slave1_port, master1_port, output_path, 1)
    _generate_slave(host, slave2_port, master0_port, output_path, 2)

    _generate_sentinel(
        host,
        sentinel_port,
        [master0_port, master1_port],
        output_path,
        SENTINEL_PARAMS,
    )


def main():
    args = _parse_args()
    generate_redis_configs(
        output_path=args.output,
        host=args.host,
        master0_port=args.master0_port,
        master1_port=args.master1_port,
        slave0_port=args.slave0_port,
        slave1_port=args.slave1_port,
        slave2_port=args.slave2_port,
        sentinel_port=args.sentinel_port,
    )


if __name__ == '__main__':
    main()
