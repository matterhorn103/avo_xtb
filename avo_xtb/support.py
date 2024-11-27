import sys
from pathlib import Path

# Manipulate the Python Path to get everything we need from the easyxtb module
sys.path.insert(0, str(Path(__file__).parent.parent / "easyxtb/src"))

# Make easyxtb available as to anything that imports support.py as if it was installed
import easyxtb


# Make sure stdout stream is always Unicode, as Avogadro 1.99 expects
sys.stdout.reconfigure(encoding="utf-8")
