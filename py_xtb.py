"""Makes everything from the py-xtb package easily available without having to install it."""

import sys
from pathlib import Path

sys.path.append(Path(__file__).parent / "py-xtb/src")

from py_xtb import *
