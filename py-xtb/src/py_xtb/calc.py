# Copyright (c) 2023-2024, Matthew J. Milner
# This file is part of py-xtb which is released under the BSD 3-Clause License.
# See LICENSE or go to https://opensource.org/license/BSD-3-clause for full details.

"""
Provides both the key `Calculation` class and a function-based calculation API.

The `Calculation` object provides the infrastructure and methods to launch a calculation
on the command line and is used by all other calculation options.

The function-based API returns just the values of interest for a given geometry in a
quick and intuitive fashion, without the user having to worry about `Calculation`
objects.

Both are designed to be run on `Geometry` objects.
"""

import os
import subprocess
from pathlib import Path
from shutil import rmtree

from .conf import XTB_BIN, CREST_BIN, TEMP_DIR
from .geometry import Geometry
from .parse import parse_energy


class Calculation:

    def __init__(
        self,
        program: str | os.PathLike = "xtb",
        runtype: str | None = None,
        runtype_args: list[str] | None = None,
        options: dict | None = None,
        command: list[str] | None = None,
        input_geometry: Geometry | None = None,
        calc_dir: os.PathLike | None = TEMP_DIR,
    ):
        """A convenience object to prepare, launch, and hold the results of
        calculations.
        
        `options` are the flags passed to be `xtb` or `crest` and should be given
        without preceding minuses, as the appropriate number will be added
        automatically.
        To use a flag that takes no argument, set the value to `True`.
        Flags with values of `False` or `None` will not be passed.
        """
        if program == "xtb":
            self.program = XTB_BIN
        elif program == "crest":
            self.program = CREST_BIN
        else:
            self.program = Path(program)

        self.runtype = runtype if runtype else "scc"
        self.runtype_args = runtype_args if runtype_args else []
        self.options = options if options else {}
        self.command = command
        self.input_geometry = input_geometry
        if calc_dir:
            self.calc_dir = Path(calc_dir)
    

    def run(self):
        """Run calculation with xtb or crest, storing the output, the saved output file,
        and the parsed energy, as well as the `subprocess` object."""

        # Make sure calculation directory exists and is empty
        if self.calc_dir.exists():
            for x in self.calc_dir.iterdir():
                if x.is_file():
                    x.unlink()
                elif x.is_dir():
                    rmtree(x)
        else:
            self.calc_dir.mkdir(parents=True)

        # Save geometry to file
        geom_file = self.calc_dir / "input.xyz"
        self.input_geometry.write_xyz(geom_file)
        # We are using proper paths for pretty much everything so it shouldn't be
        # necessary to change the working dir
        # But we do anyway to be absolutely that xtb runs correctly and puts all the
        # output here
        os.chdir(self.calc_dir)
        self.output_file = geom_file.with_name("output.out")
        
        if self.command:
            # If arguments were passed by the user, use them as is
            command = self.command
        else:
            # Build command line args
            command = [str(self.program), "--" + self.runtype, *self.runtype_args]
            for flag, value in self.options.items():
                # Add appropriate number of minuses to flags
                if len(flag) == 1:
                    flag = "-" + flag
                else:
                    flag = "--" + flag
                if value is True:
                    command.append(flag)
                elif value is False or value is None:
                    continue
                else:
                    command.extend([flag, str(value)])
        # Add geometry after a demarcating double minus
        command.extend(["--", str(geom_file)])
        print(command)
        
        # Run xtb from command line
        subproc = subprocess.run(command, capture_output=True, encoding="utf-8")

        # Store output
        self.output = subproc.stdout
        # Save to file
        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write(self.output)
        if self.program.stem == "xtb":
            # Extract energy from output
            # If not found, returns None
            self.energy = parse_energy(self.output)
        else:
            # Not yet implemented for crest
            self.energy = None
        # Store the subprocess.CompletedProcess object too
        self.subproc = subproc


def energy(
    input_geom: Geometry,
    charge: int = 0,
    multiplicity: int = 1,
    solvation: str | None = None,
    method: int = 2,
    return_calc: bool = False,
) -> float:
    """Calculate energy in hartree for given geometry."""

    unpaired_e = multiplicity - 1
    calc = Calculation(
        input_geometry=input_geom,
        options={
            "chrg": charge,
            "uhf": unpaired_e,
            "gfn": method,
            "alpb": solvation,
        },
    )
    calc.run()
    if return_calc:
        return calc.energy, calc
    else:
        return calc.energy


def optimize(
    input_geom: Geometry,
    charge: int = 0,
    multiplicity: int = 1,
    solvation: str | None = None,
    method: int = 2,
    level: str = "normal",
    return_calc: bool = False,
) -> Geometry:
    """Optimize the geometry, starting from the provided initial geometry, and return
    the optimized geometry."""

    unpaired_e = multiplicity - 1
    calc = Calculation(
        input_geometry=input_geom,
        runtype="opt",
        runtype_args=[level],
        options={
            "chrg": charge,
            "uhf": unpaired_e,
            "gfn": method,
            "alpb": solvation,
        },
    )
    calc.run()
    if return_calc:
        return calc.energy, calc
    else:
        return calc.energy


from .freq import frequencies
from .ohess import opt_freq
from .orbitals import orbitals
from .conformers import conformers
from .md import md
