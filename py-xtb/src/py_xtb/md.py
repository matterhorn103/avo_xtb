# Copyright (c) 2023-2024, Matthew J. Milner
# This file is part of py-xtb which is released under the BSD 3-Clause License.
# See LICENSE or go to https://opensource.org/license/BSD-3-clause for full details.

from pathlib import Path

from .run import run_xtb


def md(
    geom_file: Path,
    input_file: Path,
    charge: int = 0,
    multiplicity: int = 1,
    solvation: str | None = None,
) -> Path:
    """Carry out molecular dynamics simulation and return resulting trajectory as multi-geometry xyz-style .trj file."""
    spin = multiplicity - 1
    command = [
        "xtb",
        geom_file,
        "--input",
        input_file,
        "--omd",
        "--chrg",
        str(charge),
        "--uhf",
        str(spin),
    ]
    # Add solvation if requested
    if solvation is not None:
        command.append("--alpb")
        command.append(solvation)
    # Run xtb from command line
    calc, out_file, energy = run_xtb(command, geom_file)
    # Return path to trajectory file, along with energy
    return geom_file.with_name("xtb.trj")
