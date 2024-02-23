"""Provide backend functions to run any calculation on the command line, used by all calculation options."""
"""
avo_xtb
A full-featured interface to xtb in Avogadro 2.
Copyright (c) 2023, Matthew J. Milner

BSD 3-Clause License

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import os
import subprocess
from pathlib import Path

from config import xtb_bin, crest_bin


# All xtb and crest commands rely on the functionality in this module
# This thus effectively disables the menu command if executing would be impossible
if xtb_bin is None:
    raise FileNotFoundError("xtb binary not found.")
    quit()


def run_xtb(command: str, geom_file: Path) -> tuple[subprocess.CompletedProcess, Path, float]:
    """Run provided command with xtb on the command line, then return the process, the output file, and the parsed energy."""
    # Change working dir to that of geometry file to run xtb correctly
    os.chdir(geom_file.parent)
    out_file = geom_file.with_name("output.out")

    # Replace xtb with xtb path
    if command[0] == "xtb":
        command[0] = xtb_bin
    # Replace <geometry file> string with geom_file
    if "<geometry_file>" in command:
        command[command.index("<geometry_file>")] = geom_file

    # Run xtb from command line
    calc = subprocess.run(command, capture_output=True, encoding="utf-8")
    with open(out_file, "w", encoding="utf-8") as output:
        output.write(calc.stdout)
    
    # Extract energy from output stream
    # If not found, returns 0.0
    energy = parse_energy(calc.stdout)

    # Return everything as a tuple including subprocess.CompletedProcess object
    return calc, out_file, energy


# Similarly, provide a generic function to run any crest calculation
def run_crest(command: str, geom_file: Path) -> tuple[subprocess.CompletedProcess, Path]:
    """Run provided command with crest on the command line, then return the process and the output file."""
    # Change working dir to that of geometry file to run crest correctly
    os.chdir(geom_file.parent)
    out_file = geom_file.with_name("output.out")

    # Replace crest with crest path
    if command[0] == "crest":
        command[0] = crest_bin
    # Replace <geometry file> string with geom_file
    if "<geometry_file>" in command:
        command[command.index("<geometry_file>")] = geom_file

    # Run in parallel
    #os.environ["PATH"] += os.pathsep + path
    # Run crest from command line
    calc = subprocess.run(command, capture_output=True, encoding="utf-8")
    with open(out_file, "w", encoding="utf-8") as output:
        output.write(calc.stdout)

    # Return everything as a tuple including subprocess.CompletedProcess object
    return calc, out_file


def parse_energy(output_string: str) -> float:
    """Find the final energy in an xtb output file and return as a float. Units vary depending on calculation type."""
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
