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
import sys
from pathlib import Path
from shutil import rmtree, copytree

from config import config, calc_dir
from run import run_xtb


def md(
        geom_file: Path,
        input_file: Path,
        charge: int = 0,
        multiplicity: int = 1,
        solvation: str | None = None,
        ) -> Path:
    """Carry out molecular dynamics simulation and return resulting trajectory as multi-geometry xyz-style .trj file."""
    spin = multiplicity - 1
    command = ["xtb", geom_file, "--input", input_file, "--omd", "--chrg", str(charge), "--uhf", str(spin)]
    # Add solvation if requested
    if solvation is not None:
        command.append("--alpb")
        command.append(solvation)
    # Run xtb from command line
    calc, out_file, energy = run_xtb(command, geom_file)
    # Return path to trajectory file, along with energy
    return geom_file.with_name("xtb.trj")


#def parse_trajectory(trj_file):


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
        options = {
            "inputMoleculeFormat": "xyz",
            "userOptions": {
                "dump": {
                    "type": "float",
                    "label": "Printout interval",
                    "default": 50.0,
                    "minimum": 1.0,
                    "maximum": 1000.0,
                    "suffix": " fs"
                },
                "hmass": {
                    "type": "integer",
                    "label": "Mass of hydrogen atoms",
                    "default": 4,
                    "minimum": 1,
                    "suffix": " times"
                },
                "nvt": {
                    "type": "boolean",
                    "label": "Perform simulation in NVT ensemble",
                    "default": True
                },
                "temp": {
                    "type": "float",
                    "label": "Thermostat temperature",
                    "default": 298.15,
                    "minimum": 0.00,
                    "maximum": 10000.00,
                    "suffix": " K"
                },
                "time": {
                    "type": "float",
                    "label": "Total run time of simulation",
                    "default": 50.0,
                    "minimum": 0.1,
                    "maximum": 10000.0,
                    "suffix": " ps"
                },
                "sccacc": {
                    "type": "float",
                    "label": "Accuracy of xTB calculations",
                    "default": 2.0,
                    "minimum": 0.1,
                },
                "shake": {
                    "type": "integer",
                    "label": ("Use SHAKE algorithm to constrain bonds\n"
                              "0 = off, 1 = X-H only, 2 = all bonds"),
                    "default": 2,
                    "minimum": 0
                },
                "step": {
                    "type": "float",
                    "label": "Time step for propagation",
                    "default": 4.0,
                    "minimum": 0.1,
                    "maximum": 100.0,
                    "suffix": " fs"
                },
                "save_dir": {
                    "type": "string",
                    "label": "Save results in",
                    "default": "<plugin_directory>/last"
                }
            }
        }
        print(json.dumps(options))

    if args.display_name:
        print("Molecular Dynamics…")
    if args.menu_path:
        print("Extensions|Semi-empirical (xtb){740}")

    if args.run_command:
        # Remove results of last calculation
        if calc_dir.exists():
            rmtree(calc_dir)
        calc_dir.mkdir()

        # Read input from Avogadro
        avo_input = json.loads(sys.stdin.read())
        # Extract the coords and write to file for use as xtb input
        geom = avo_input["xyz"]
        xyz_path = calc_dir / "input.xyz"
        with open(xyz_path, "w", encoding="utf-8") as xyz_file:
            xyz_file.write(str(geom))
        
        # Write all MD options to input file
        input_path = xyz_path.with_name("md.inp")
        with open(input_path, "w", encoding="utf-8") as input_file:
            input_file.write("$md")
            for key, value in avo_input.items():
                if key not in ["xyz", "save_dir"]:
                    input_file.write(f"   {key}={value}")
            input_file.write("$end")

        # Run calculation using xyz file and input file
        trj_path = md(
            xyz_path,
            input_path,
            charge=avo_input["charge"],
            multiplicity=avo_input["spin"],
            solvation=config["solvent"]
            )

        # Make sure that the calculation was successful before investing any more time
        if not trj_path.with_name("xtbmdok").exists():
            result = {"message": "MD failed!"}
            print(json.dumps(result))
            exit()

        # Format everything appropriately for Avogadro
        # Start by passing back the original cjson, then add changes
        result = {"moleculeFormat": "cjson", "cjson": avo_input["cjson"]}

        # Make sure the list of lists is already in place in the cjson
        result["cjson"]["atoms"]["coords"]["3dSets"] = []

        # The geometries are contained in a trajectory file
        # Read line by line and add manually to cjson style, splitting by structure
        n_atoms = int(avo_input["xyz"].split()[0])
        with open(trj_path, encoding="utf-8") as trj_file:
            structure_number = -1
            while True:
                line = trj_file.readline().strip()
                if line == "":
                    # End of file
                    break
                elif line.split()[0] == str(n_atoms):
                    # Move to next element of 3dSet
                    structure_number += 1
                    # Add an empty list to contain the coordinates
                    result["cjson"]["atoms"]["coords"]["3dSets"].append([])
                    continue
                elif line.split()[0] == "energy:":
                    # Ignore energies for now
                    continue
                else:
                    # This is an actual atom!
                    xyz = [float(x) for x in line.split()[1:]]
                    # Add to list of coordinates at appropriate index of 3dSets
                    result["cjson"]["atoms"]["coords"]["3dSets"][structure_number].extend(xyz)

        # If user specified a save location, copy calculation directory to there
        if avo_input["save_dir"] != "<plugin_directory>/last":
            copytree(calc_dir, Path(avo_input["save_dir"]), dirs_exist_ok=True)

        # Save result
        with open(calc_dir / "result.cjson", "w", encoding="utf-8") as save_file:
            json.dump(result["cjson"], save_file, indent=2)
        # Pass back to Avogadro
        print(json.dumps(result, indent=2))