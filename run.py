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

from config import config, xtb_bin, calc_dir
import convert


def run_xtb(command, geom_file):
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
    return (calc, out_file, energy)


def parse_energy(output_string):
    # Get final energy from output file
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
                    "default": str(calc_dir),
                    "order": 1.0
                    },
                #"Number of threads": {
                #    "type": "integer",
                #    #"label": "Number of cores",
                #    "minimum": 1,
                #    "default": 1,
                #    "order": 2.0
                #    },
                #"Memory per core": {
                #    "type": "integer",
                #    #"label" "Memory per core",
                #    "minimum": 1,
                #    "default": 1,
                #    "suffix": " GB",
                #    "order": 3.0
                #    },
                "command": {
                    "type": "string",
                    "label": "Command to run",
                    "default": "xtb <geometry_file> --opt --chrg 0 --uhf 0",
                    "order": 10.0
                    },
                "help": {
                    "type": "text",
                    "label": "For help see",
                    "default": "https://xtb-docs.readthedocs.io/",
                    "order": 9.0
                    },
                "turbomole": {
                    "type": "boolean",
                    "label": "Use Turbomole geometry\n(use for periodic systems)",
                    "default": False,
                    "order": 4.0
                    }
                }
            }
        # Add solvation to default command if found in user config
        if config["solvent"] is not None:
            options["userOptions"]["command"]["default"] += f" --alpb {config['solvent']}"
        print(json.dumps(options))
    if args.display_name:
        print("Run…")
    if args.menu_path:
        # Only show menu option if xtb binary was found
        if xtb_bin is not None:
            print("Extensions|Semi-empirical (xtb){350}")
        else:
            pass

    if args.run_command:
        # Remove results of last calculation
        if calc_dir.exists():
            rmtree(calc_dir)
        Path.mkdir(calc_dir)

        # Read input from Avogadro
        avo_input = json.loads(sys.stdin.read())

        # Extract the coords and write to file for use as xtb input
        geom = avo_input["tmol"]
        tmol_path = Path(calc_dir) / "input.tmol"
        with open(tmol_path, "w", encoding="utf-8") as tmol_file:
            tmol_file.write(str(geom))
        # Convert to xyz format
        xyz_path = convert.tmol_to_xyz(tmol_path)
        # Select geometry to use on basis of user choice
        if avo_input["turbomole"]:
            geom_path = tmol_path
        else:
            geom_path = xyz_path

        # Run calculation; returns subprocess.CompletedProcess object and path to output.out
        calc, result_path, energy = run_xtb(
            avo_input["command"].split(),
            geom_path
            )

        # Format everything appropriately for Avogadro
        # Start by passing back the original cjson, then add changes
        result = {"moleculeFormat": "cjson", "cjson": avo_input["cjson"]}

        # Many different parts of the following may wish to report message
        # Instantiate a message list and combine later
        message = []

        # Catch errors in xtb execution (to do)
        #except Exception as ex:
            #print(str(ex))
        #if (error condition):
            #result["message"] = "Error message"
            # Pass back to Avogadro
            #print(json.dumps(result))
            #break

        # Check if opt was requested
        if any(x in avo_input["command"] for x in ["--opt", "--ohess"]):
            # Convert geometry
            if geom_path.suffix == ".tmol":
                geom_cjson_path = convert.tmol_to_cjson(result_path.with_name("xtbopt.tmol"))
            else:
                geom_cjson_path = convert.xyz_to_cjson(result_path.with_name("xtbopt.xyz"))
            # Open the cjson
            with open(geom_cjson_path, encoding="utf-8") as result_cjson:
                geom_cjson = json.load(result_cjson)
            result["cjson"]["atoms"]["coords"] = geom_cjson["atoms"]["coords"]

        # Check if frequencies were requested
        if any(x in avo_input["command"] for x in ["--hess", "--ohess"]):
            freq_cjson_path = convert.g98_to_cjson(result_path.with_name("g98.out"))
            # Open the cjson
            with open(freq_cjson_path, encoding="utf-8") as result_cjson:
                freq_cjson = json.load(result_cjson)
            result["cjson"]["vibrations"] = freq_cjson["vibrations"]
            # xtb no longer gives Raman intensities but does write them as all 0
            # If passed on to the user this is misleading so remove them
            if "ramanIntensities" in result["cjson"]["vibrations"]:
                del result["cjson"]["vibrations"]["ramanIntensities"]
            # Inform user if there are negative frequencies
            if float(freq_cjson["vibrations"]["frequencies"][0]) < 0:
                # Check to see if xtb has produced a distorted geometry (ohess does this)
                distorted_geom = geom_path.with_stem("xtbhess")
                if distorted_geom.exists():
                    message.append("At least one negative frequency found!\n"
                                   "This is not a minimum on the potential energy surface.\n"
                                   "You should reoptimize the geometry starting from the\n"
                                   "distorted geometry found in the calculation directory\n"
                                   "with the filename 'xtbhess.xyz' or 'xtbhess.tmol'.")
                else:
                    message.append("At least one negative frequency found!\n"
                                   "This is not a minimum on the potential energy surface.\n"
                                   "You should reoptimize the geometry.")
            
        # Check if orbitals were requested
        # (to do)
        # Not sure how this will be possible at the same time as any other calculation type
        # Currently avo only accepts one file format being passed back
        #if "--molden" in command

        # Add energy from output
        energy = parse_energy(calc.stdout)
        # Convert energy to eV for Avogadro
        energy_eV = convert.convert_energy(energy, "hartree")["eV"]
        result["cjson"]["properties"]["totalEnergy"] = str(round(energy_eV, 7))

        # Add all the messages, separated by blank lines
        result["message"] = "\n\n".join(message)

        # Save result
        with open(calc_dir / "result.cjson", "w", encoding="utf-8") as save_file:
            json.dump(result["cjson"], save_file, indent=2)

        # If user specified a save location, copy calculation directory to there
        if Path(avo_input["save_dir"]) != calc_dir:
            copytree(calc_dir, Path(avo_input["save_dir"]), dirs_exist_ok=True)

        # Pass back to Avogadro
        print(json.dumps(result))
