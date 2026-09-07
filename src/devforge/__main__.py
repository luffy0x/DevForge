import sys

from .cli import main as scan_main
from .claim_cli import main as claim_main
from .contribute_cli import main as contribute_main
from .retry_cli import main as retry_main


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "claim":
        sys.argv = [sys.argv[0], *sys.argv[2:]]
        raise SystemExit(claim_main())
    if len(sys.argv) > 1 and sys.argv[1] == "contribute":
        sys.argv = [sys.argv[0], *sys.argv[2:]]
        raise SystemExit(contribute_main())
    if len(sys.argv) > 1 and sys.argv[1] == "retry":
        sys.argv = [sys.argv[0], *sys.argv[2:]]
        raise SystemExit(retry_main())
    raise SystemExit(scan_main())
