# Copyright (c) 2023-2024, Matthew J. Milner
# This file is part of py-xtb which is released under the BSD 3-Clause License.
# See LICENSE or go to https://opensource.org/license/BSD-3-clause for full details.

import argparse
import json
import sys
from shutil import rmtree
from pathlib import Path

from config import config, calc_dir
from .run import run_xtb


def orbitals(
    geom_file: Path,
    charge: int = 0,
    multiplicity: int = 1,
    solvation: str | None = None,
    method: int = 2,
) -> Path:
    """Calculate molecular orbitals for given geometry, return file in Molden format."""
    spin = multiplicity - 1
    # Just do a single point calculation but pass molden option to get orbital printout
    command = [
        "xtb",
        geom_file,
        "--molden",
        "--chrg",
        str(charge),
        "--uhf",
        str(spin),
        "--gfn",
        str(method),
    ]
    # Add solvation if requested
    if solvation is not None:
        command.extend(["--alpb", solvation])
    # Run xtb from command line
    calc, out_file, energy = run_xtb(command, geom_file)

    # Return path to molden file
    return geom_file.with_name("molden.input")
