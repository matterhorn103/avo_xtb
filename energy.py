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


def energy(geom_file, charge=0, multiplicity=1):
    # Change working dir to this one to run xtb correctly
    os.chdir(geom_file.parent)
    out_file = geom_file.with_name("output.out")
    spin = multiplicity - 1
    command = [xtb_bin, geom_file, "--chrg", str(charge), "--uhf", str(spin)]
    # Run xtb from command line
    calc = subprocess.run(command, capture_output=True, encoding="utf-8")
    with open(out_file, "w") as output:
        output.write(calc.stdout)
    energy = parse_energy(calc.stdout)
    return energy


def parse_energy(output_string):
    end = output_string.split("\n")[-20:]
    matched_lines = [line for line in end if "TOTAL ENERGY" in line]
    if len(matched_lines) > 0:
        energy_line = matched_lines[-1]
    else:
        # Placeholder result to avoid errors for now
        energy_line = "0.0"
    for section in energy_line.split():
        try:
            energy = float(section)
        except ValueError:
            continue
    return energy


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
        print("Energy")
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
        xyz_path = Path(calc_dir) / "input.coord"
        with open(xyz_path, "w", encoding="utf-8") as xyz_file:
            xyz_file.write(str(geom))

        # Run calculation; returns energy as float in hartree
        energy = energy(
            xyz_path,
            avo_input["charge"],
            avo_input["spin"]
            )
        # Convert energy to eV for Avogadro
        energy_eV = energy * 27.211386245
        # Format everything appropriately for Avogadro
        # Start by passing back the original cjson, then add changes
        result = {"molecularFormat": "cjson", "cjson": avo_input["cjson"]}
        # Currently Avogadro ignores the energy result
        result["message"] = f"Energy:\n{str(round(energy, 7))} hartree\n{str(round(energy_eV, 7))} eV"
        result["cjson"]["properties"]["totalEnergy"] = str(round(energy_eV, 7))
        # Pass back to Avogadro
        print(json.dumps(result))
