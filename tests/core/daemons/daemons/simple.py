#!/usr/bin/env python3

import argparse
import sys
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('cmd', help='Command')
    args = parser.parse_args()

    if args.cmd == 'pass':
        pass
    elif args.cmd == 'hello':
        print('hello, world')
    elif args.cmd == 'stdout':
        for i in range(3):
            print(f'out{i}', file=sys.stdout)
            print(f'err{i}', file=sys.stderr)
            time.sleep(0.01)
    else:
        raise RuntimeError(f'Unknown command {args.cmd}')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
