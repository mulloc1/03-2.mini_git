"""python -m mini_git module entrypoint."""

from __future__ import annotations

import sys

from mini_git.main import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
