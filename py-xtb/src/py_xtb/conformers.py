# Copyright (c) 2023-2024, Matthew J. Milner
# This file is part of py-xtb which is released under the BSD 3-Clause License.
# See LICENSE or go to https://opensource.org/license/BSD-3-clause for full details.

from pathlib import Path

from .conf import XTB_BIN, CREST_BIN
from .run import run_crest


def conformers(
    geom_file: Path,
    charge: int = 0,
    multiplicity: int = 1,
    solvation: str | None = None,
    ewin: int | float = 6,
    hess: bool = False,
) -> Path:
    """Simulate a conformer ensemble and return multi-geometry xyz file.

    All conformers within <ewin> kcal/mol are kept.
    If hess=True, vibrational frequencies are calculated and the conformers reordered by Gibbs energy.
    """
    unpaired_e = multiplicity - 1
    command = [
        CREST_BIN,
        geom_file,
        "--xnam",
        XTB_BIN,
        "--chrg",
        str(charge),
        "--uhf",
        str(unpaired_e),
        "--ewin",
        str(ewin),
    ]
    # Add solvation if requested
    if solvation is not None:
        command.append("--alpb")
        command.append(solvation)
    if hess:
        command.extend(["--prop", "hess"])

    # Run crest from command line
    calc, out_file = run_crest(command, geom_file)

    return geom_file.with_stem("crest_conformers")
