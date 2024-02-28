"""User-facing command to run any arbitrary xtb command."""
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

from config import config, xtb_bin, crest_bin, calc_dir
import convert
import obabel_convert
from run import run_xtb, parse_energy


# Define behaviour of Run menu command
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
                    "order": 1.0,
                    },
                #"Number of threads": {
                #    "type": "integer",
                #    #"label": "Number of cores",
                #    "minimum": 1,
                #    "default": 1,
                #    "order": 2.0,
                #    },
                #"Memory per core": {
                #    "type": "integer",
                #    #"label" "Memory per core",
                #    "minimum": 1,
                #    "default": 1,
                #    "suffix": " GB",
                #    "order": 3.0,
                #    },
                "command": {
                    "type": "string",
                    "label": "Command to run",
                    "default": f"xtb <geometry_file> --opt {config["level"]} --chrg 0 --uhf 0",
                    "order": 10.0,
                    },
                "help": {
                    "type": "text",
                    "label": "For help see",
                    "default": "https://xtb-docs.readthedocs.io/",
                    "order": 9.0,
                    },
                "turbomole": {
                    "type": "boolean",
                    "label": "Use Turbomole geometry\n(use for periodic systems)",
                    "default": False,
                    "order": 4.0,
                    }
                }
            }
        # Add solvation to default command if found in user config
        if config["solvent"] is not None:
            options["userOptions"]["command"]["default"] += f" --alpb {config['solvent']}"
        # Add method to default command but only if not the default (currently GFN2-xTB)
        if config["method"] != 2:
            options["userOptions"]["command"]["default"] += f" --gfn {config['method']}"
        print(json.dumps(options))
    if args.display_name:
        print("Run…")
    if args.menu_path:
        print("Extensions|Semi-empirical (xtb){350}")

    if args.run_command:
        # Remove results of last calculation
        if calc_dir.exists():
            for x in calc_dir.iterdir():
                if x.is_file():
                    x.unlink()
                elif x.is_dir():
                    rmtree(x)

        # Read input from Avogadro
        avo_input = json.loads(sys.stdin.read())

        # Extract the coords and write to file for use as xtb input
        # Select geometry to use on basis of user choice
        if avo_input["turbomole"]:
            tmol_path = Path(calc_dir) / "input.tmol"
            with open(tmol_path, "w", encoding="utf-8") as tmol_file:
                # Avogadro seems to pass tmol string with \r\n newlines on Windows
                # Python writes \r\n as \r\r\n on Windows
                # Open Babel then reads two new lines not one
                # So make sure we only have Python newlines (\n) by removing any \r
                tmol_str = str(avo_input["tmol"]).replace("\r", "")
                tmol_file.write(tmol_str)
            geom_path = tmol_path
        else:
            # Use xyz - first get xyz format (as list of lines) from cjson
            xyz = convert.cjson_to_xyz(avo_input["cjson"], lines=True)
            # Save to file, don't forget to add newlines
            xyz_path = Path(calc_dir) / "input.xyz"
            with open(xyz_path, "w", encoding="utf-8") as xyz_file:
                xyz_file.write("\n".join(xyz))
            geom_path = xyz_path

        # Run calculation; returns subprocess.CompletedProcess object and path to output.out
        calc, result_path, energy = run_xtb(
            avo_input["command"].split(),
            geom_path,
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
            if geom_path.suffix == ".tmol":
                # Convert geometry with Open Babel
                geom_cjson_path = obabel_convert.tmol_to_cjson(result_path.with_name("xtbopt.tmol"))
                # Open the generated cjson
                with open(geom_cjson_path, encoding="utf-8") as result_cjson:
                    geom_cjson = json.load(result_cjson)
            else:
                # Read the xyz file
                with open(result_path.with_name("xtbopt.xyz"), encoding="utf-8") as result_xyz:
                    xyz = result_xyz.read().split("\n")
                # Convert geometry without Open Babel
                geom_cjson = convert.xyz_to_cjson(xyz_lines=xyz)
            result["cjson"]["atoms"]["coords"] = geom_cjson["atoms"]["coords"]

        # Check if frequencies were requested
        if any(x in avo_input["command"] for x in ["--hess", "--ohess"]):
            freq_cjson_path = obabel_convert.g98_to_cjson(result_path.with_name("g98.out"))
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
        if not (avo_input["save_dir"] in ["", None] or Path(avo_input["save_dir"]) == calc_dir):
            copytree(calc_dir, Path(avo_input["save_dir"]), dirs_exist_ok=True)

        # Pass back to Avogadro
        print(json.dumps(result))