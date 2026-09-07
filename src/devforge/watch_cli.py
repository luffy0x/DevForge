import argparse
import time

from .cli import main as scan_main


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="devforge watch", add_help=False)
    parser.add_argument("--interval", type=int, default=300)
    parser.add_argument("--once", action="store_true")
    args, scan_args = parser.parse_known_args(argv)
    if args.interval <= 0:
        parser.error("--interval must be greater than zero")

    try:
        while True:
            result = scan_main(scan_args)
            if args.once:
                return result
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("watch stopped")
        return 0
