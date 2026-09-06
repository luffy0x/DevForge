import sys

from .cli import main as scan_main
from .claim_cli import main as claim_main


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "claim":
        sys.argv = [sys.argv[0], *sys.argv[2:]]
        raise SystemExit(claim_main())
    raise SystemExit(scan_main())
