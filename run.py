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
from shutil import rmtree, copytree

from config import xtb_bin, plugin_dir
import convert
from energy import parse_energy


def run(geom_file, command_string):
    # Change working dir to this one to run xtb correctly
    os.chdir(geom_file.parent)
    out_file = geom_file.with_name("output.out")
    command = command_string.split()
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
    energy = parse_energy(calc.stdout)
    return (out_file, energy)


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
            "inputMoleculeFormat": "tmol",
            "userOptions": {
                "save_dir": {
                    "type": "string",
                    "label": "Save results in",
                    "default": "<plugin_directory>/last"
                    },
                "Number of cores": {
                    "type": "integer",
                    #"label": "Number of cores",
                    "minimum": 1,
                    "default": 1
                    },
                "Memory per core": {
                    "type": "integer",
                    #"label" "Memory per core",
                    "minimum": 1,
                    "default": 1,
                    "suffix": " GB"
                    },
                "command": {
                    "type": "string",
                    "label": "Command to run",
                    "default": "xtb <geometry_file> --opt --chrg 0 --uhf 0"
                    },
                "turbomole": {
                    "type": "boolean",
                    "label": "Use Turbomole geometry\n(use for periodic systems)",
                    "default": False
                    }
                }
            }
        print(json.dumps(options))
    if args.display_name:
        print("Run…")
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
        geom = avo_input["tmol"]
        coord_path = Path(calc_dir) / "input.coord"
        with open(coord_path, "w", encoding="utf-8") as coord_file:
            coord_file.write(str(geom))
        # Convert to xyz format
        xyz_path = convert.coord_to_xyz(coord_path)
        # Select geometry to use on basis of user choice
        if avo_input["turbomole"]:
            geom_path = coord_path
        else:
            geom_path = xyz_path

        # Run calculation; returns path to output.out and energy
        result_path, energy = run(
            geom_path,
            avo_input["command"]
            )

        # Format everything appropriately for Avogadro
        # Start by passing back the original cjson, then add changes
        result = {"molecularFormat": "cjson", "cjson": avo_input["cjson"]}

        # Catch errors in xtb execution (to do)
        #if (error condition):
            #result["message"] = "Error message"
            # Pass back to Avogadro
            #print(json.dumps(result))
            #break

        # Check if opt was requested
        if any(x in avo_input["command"] for x in ["--opt", "--ohess"]):
            # Convert geometry
            cjson_path = convert.xyz_to_cjson(result_path.with_name("xtbopt.xyz"))
            # Open the cjson
            with open(cjson_path, encoding="utf-8") as result_cjson:
                cjson_geom = json.load(result_cjson)
            result["cjson"]["atoms"]["coords"] = cjson_geom["atoms"]["coords"]

        # Check if frequencies were requested
        # (to do)
        #if any(x in avo_input["command"] for x in ["--hess", "--ohess"]):

        # Check if orbitals were requested
        # (to do)
        #if "--molden" in command

        # Add energy from output file
        # Convert energy to eV for Avogadro
        energy_eV = energy * 27.211386245
        result["cjson"]["properties"]["totalEnergy"] = str(round(energy_eV, 7))

        # Save result
        with open(calc_dir / "result.cjson", "w", encoding="utf-8") as save_file:
            json.dump(result["cjson"], save_file)

        # If user specified a save location, copy calculation directory to there
        if avo_input["save_dir"] != "<plugin_directory>/last":
            copytree(calc_dir, Path(avo_input["save_dir"]), dirs_exist_ok=True)

        # Pass back to Avogadro
        print(json.dumps(result))
