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
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from shutil import rmtree

from config import xtb_bin, plugin_dir


def orbitals(geom_file, charge=0, multiplicity=1):
    # Change working dir to this one to run xtb correctly
    os.chdir(geom_file.parent)
    out_file = geom_file.with_name("output.out")
    spin = multiplicity - 1
    # Just do a single point calculation but pass molden option to get orbital printout
    command = [xtb_bin, geom_file, "--molden", "--chrg", str(charge), "--uhf", str(spin)]
    # Run xtb from command line
    calc = subprocess.run(command, capture_output=True, encoding="utf-8")
    with open(out_file, "w", encoding="utf-8") as output:
        output.write(calc.stdout)
    # Return path to molden file
    return (geom_file.with_name("molden.input"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--print-options", action="store_true")
    parser.add_argument("--run-command", action="store_true")
    parser.add_argument("--display-name", action="store_true")
    parser.add_argument("--lang", nargs="?", default="en")
    parser.add_argument("--menu-path", action="store_true")
    args = parser.parse_args()

    if args.print_options:
        options = {"inputMoleculeFormat": "xyz"}
        print(json.dumps(options))
    if args.display_name:
        print("Orbitals")
    if args.menu_path:
        print("Extensions|Semi-empirical (xtb)")

    if args.run_command:
        # Run calculation within plugin directory
        calc_dir = plugin_dir / "last"
        # Remove results of last calculation
        if calc_dir.exists():
            rmtree(calc_dir)
        Path.mkdir(calc_dir)

        # Read input from Avogadro
        avo_input = json.loads(sys.stdin.read())
        # Extract the coords and write to file for use as xtb input
        geom = avo_input["xyz"]
        xyz_path = calc_dir / "input.xyz"
        with open(xyz_path, "w", encoding="utf-8") as xyz_file:
            xyz_file.write(str(geom))

        # Run calculation using xyz file
        result_path = orbitals(
            xyz_path,
            avo_input["charge"],
            avo_input["spin"]
            )

        # Get molden file as string
        with open(result_path, encoding="utf-8") as molden_file:
            molden_string = molden_file.read()
        # Format everything appropriately for Avogadro
        # Just pass orbitals file with append
        result = {"append": True, "molecularFormat": "molden", "molden": molden_string}
        # Pass back to Avogadro
        print(json.dumps(result))
