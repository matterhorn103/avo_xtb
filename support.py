import sys
from pathlib import Path

# Manipulate the Python Path to get everything we need from the py_xtb module
sys.path.insert(0, str(Path(__file__).parent / "py-xtb/src"))

# Make py-xtb available as to anything that imports support.py as if it was installed
import py_xtb
