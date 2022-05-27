#!/usr/bin/env python3

import argparse
import contextlib
import os
import sys
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--timeout', help='Time before action', type=float)
    parser.add_argument(
        '--exit-code', help='Exit with specified code', type=int,
    )
    parser.add_argument(
        '--raise-signal', help='Raise specified signal', type=int,
    )
    args = parser.parse_args()

    if args.raise_signal:
        if args.timeout:
            time.sleep(args.timeout)
        pid = os.getpid()
        os.kill(pid, args.raise_signal)
    elif args.exit_code:
        if args.timeout:
            time.sleep(args.timeout)
        sys.exit(args.exit_code)
    else:
        with contextlib.closing(sys.stdout):
            print('ready', flush=True)
        while True:
            time.sleep(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
