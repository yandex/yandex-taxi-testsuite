import argparse
import pathlib
import string

CONF_TPL_FILENAME = 'redis.conf.tpl'


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--output', required=True, type=pathlib.Path,
        help='Path to output directory',
    )
    parser.add_argument(
        '--host', default='localhost',
        help='Redis host for config',
    )
    parser.add_argument(
        '--port-min', type=int, default=7000, 
        help='The start of the redis cluster port range',
    )
    parser.add_argument(
        '--port-max', type=int, default=7005, 
        help='The end of the redis cluster port range',
    )
    return parser.parse_args()


def _generate_redis_config(
        input_file: pathlib.Path,
        output_file: pathlib.Path,
        host: str,
        port: int
) -> None:
    config_tpl = input_file.read_text()
    config_body = string.Template(config_tpl).substitute(
        host=host,
        port=port,
    )
    output_file.write_text(config_body)


def _construct_output_filename(
        output_path: pathlib.Path, number: int,
) -> pathlib.Path:
    config_filename = 'redis_%s.conf' % number
    return output_path / config_filename


def _redis_config_directory() -> pathlib.Path:
    return pathlib.Path(__file__).parent / 'configs'


def generate_redis_configs(
        output_path: pathlib.Path,
        host: str,
        port_min: int,
        port_max: int,
) -> None:
    for port in range(port_min, port_max + 1):
        input_file = _redis_config_directory() / CONF_TPL_FILENAME
        output_file = _construct_output_filename(output_path, port)
        _generate_redis_config(input_file, output_file, host, port)


def main():
    args = _parse_args()
    generate_redis_configs(
        output_path=args.output,
        host=args.host,
        port_min=args.port_min,
        port_max=args.port_max,
    )


if __name__ == '__main__':
    main()
