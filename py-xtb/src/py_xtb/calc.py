"""
Function-based API where functions directly return just the calculated values.

The functions are designed to be run on a `Geometry` object.
"""

from .run import Calculation
from .energy import energy
from .opt import optimize
from .freq import frequencies
from .ohess import opt_freq
from .orbitals import orbitals
from .conformers import conformers
from .md import md
