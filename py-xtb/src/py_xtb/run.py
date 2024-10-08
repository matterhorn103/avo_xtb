# Copyright (c) 2023-2024, Matthew J. Milner
# This file is part of py-xtb which is released under the BSD 3-Clause License.
# See LICENSE or go to https://opensource.org/license/BSD-3-clause for full details.

"""
Provide backend functions to run any calculation on the command line.
Used by all calculation options.
"""

import os
import subprocess
from pathlib import Path
from shutil import rmtree

from .conf import XTB_BIN, CREST_BIN, TEMP_DIR
from .geometry import Geometry


class Calculation:

    def __init__(
        self,
        program: str | os.PathLike = "xtb",
        runtype: str | None = None,
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
        self.options = options
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
            command = [str(self.program), self.runtype]
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
        command.extend(["--", geom_file])
        
        # Run xtb from command line
        calc = subprocess.run(command, capture_output=True, encoding="utf-8")

        # Store output
        self.output = calc.stdout
        # Save to file
        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write(self.output)
        if self.program.stem == "xtb":
            # Extract energy from output
            # If not found, returns 0.0
            self.energy = parse_energy(self.output)
        else:
            # Not yet implemented for crest
            self.energy = None
        # Store the subprocess.CompletedProcess object too
        self.subproc = calc


def parse_energy(output_string: str) -> float:
    """Find the final energy in an xtb output file and return as a float.
    
    Units vary depending on calculation type."""
    # but don't convert here as not all calculation types give in same units
    end = output_string.split("\n")[-20:]
    matched_lines = [line for line in end if "TOTAL ENERGY" in line]
    if len(matched_lines) > 0:
        energy_line = matched_lines[-1]
    else:
        # Placeholder result so that something is always returned
        energy_line = "0.0"
    for section in energy_line.split():
        try:
            energy = float(section)
        except ValueError:
            continue
    return energy


### DEPRECATED ###
# These are only kept here for now to avoid import errors while everything is
# transferred to new interface

def run_xtb(
    command: list[str], input_geom: Geometry
) -> tuple[subprocess.CompletedProcess, Path, float]:
    """Run provided command with xtb on the command line, then return the process, the
    output file, and the parsed energy."""
    # Save geometry to file
    geom_file = input_geom.write_xyz(TEMP_DIR)
    # Change working dir to that of geometry file to run xtb correctly
    os.chdir(geom_file.parent)
    output_file = geom_file.with_name("output.out")

    # Replace xtb string with xtb path
    if command[0] == "xtb":
        command[0] = XTB_BIN
    # Add geom file to command string
    command.extend(["--", geom_file])

    # Run xtb from command line
    calc = subprocess.run(command, capture_output=True, encoding="utf-8")
    with open(output_file, "w", encoding="utf-8") as output:
        output.write(calc.stdout)

    # Extract energy from output stream
    # If not found, returns 0.0
    energy = parse_energy(calc.stdout)

    # Return everything as a tuple including subprocess.CompletedProcess object
    return calc, output_file, energy

# Similarly, provide a generic function to run any crest calculation
def run_crest(
    command: list[str], input_geom: Geometry
) -> tuple[subprocess.CompletedProcess, Path]:
    """Run provided command with crest on the command line, then return the process and
    the output file."""
    # Save geometry to file
    geom_file = input_geom.write_xyz(TEMP_DIR)
    # Change working dir to that of geometry file to run crest correctly
    os.chdir(geom_file.parent)
    output_file = geom_file.with_name("output.out")

    # Replace crest with crest path
    if command[0] == "crest":
        command[0] = CREST_BIN
    # Add geom file to command string
    command.extend(["--", geom_file])

    # Run in parallel
    # os.environ["PATH"] += os.pathsep + path
    # Run crest from command line
    calc = subprocess.run(command, capture_output=True, encoding="utf-8")
    with open(output_file, "w", encoding="utf-8") as output:
        output.write(calc.stdout)

    # Return everything as a tuple including subprocess.CompletedProcess object
    return calc, output_file

