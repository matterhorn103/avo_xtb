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

from config import config, calc_dir, xtb_bin, crest_bin, config_file


# Disable if xtb and crest missing
if xtb_bin is None or crest_bin is None:
    quit()


def run_crest(command, geom_file, charge=0, multiplicity=1):
    # Change working dir to that of geometry file to run crest correctly
    os.chdir(geom_file.parent)
    out_file = geom_file.with_name("output.out")

    # Run in parallel
    #os.environ["PATH"] += os.pathsep + path

    # Run crest from command line
    calc = subprocess.run(command, capture_output=True, encoding="utf-8")
    with open(out_file, "w", encoding="utf-8") as output:
        output.write(calc.stdout)

    return (geom_file.with_stem("crest_conformers"))


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
                "crest_bin": {
                    "type": "string",
                    "label": "Location of the crest binary",
                    "default": str(crest_bin),
                    "order": 1.0
                },
                "save_dir": {
                    "type": "string",
                    "label": "Save results in",
                    "default": str(calc_dir),
                    "order": 2.0
                    },
                #"Number of threads": {
                #    "type": "integer",
                #    #"label": "Number of cores",
                #    "minimum": 1,
                #    "default": 1,
                #    "order": 3.0
                #    },
                #"Memory per core": {
                #    "type": "integer",
                #    #"label" "Memory per core",
                #    "minimum": 1,
                #    "default": 1,
                #    "suffix": " GB",
                #    "order": 4.0
                #    },
                "help": {
                    "type": "text",
                    "label": "For help see",
                    "default": "https://crest-lab.github.io/crest-docs/",
                    "order": 9.0
                    },
                "solvent": {
                    "type": "stringList",
                    "label": "Solvation",
                    "values": [
                        "none",
                        "acetone",
                        "acetonitrile",
                        "aniline",
                        "benzaldehyde",
                        "benzene",
                        "ch2cl2",
                        "chcl3",
                        "cs2",
                        "dioxane",
                        "dmf",
                        "dmso",
                        "ether",
                        "ethylacetate",
                        "furane",
                        "hexandecane",
                        "hexane",
                        "methanol",
                        "nitromethane",
                        "octanol",
                        "woctanol",
                        "phenol",
                        "toluene",
                        "thf",
                        "water"
                        ],
                    "default": 0,
                    "order": 6.0
                    },
                "ewin": {
                    "type": "integer",
                    "label": "Keep all conformers within",
                    "default": 25,
                    "minimum": 1,
                    "maximum": 1000,
                    "suffix": " kJ/mol",
                    "order": 7.0
                },
                "hess": {
                    "type": "boolean",
                    "label": "Calculate frequencies for conformers\nand re-weight ensemble on free energies",
                    "default": False,
                    "order": 8.0
                }
                }
            }
        # Display energy in kcal if user has insisted on it
        if config["energy_units"] == "kcal/mol":
            options["userOptions"]["ewin"]["default"] = 6
            options["userOptions"]["ewin"]["suffix"] = " kcal/mol"
        # Make solvation default if found in user config
        if config["solvent"] is not None:
            options["userOptions"]["solvent"]["default"] = config["solvent"]
        print(json.dumps(options))
    if args.display_name:
        print("Conformers…")
    if args.menu_path:
        # Only show menu option if crest binary was found
        if crest_bin is not None:
            print("Extensions|Semi-empirical (xtb){770}")
        else:
            pass

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

        # If provided crest path different to that stored, use it and save it
        if Path(avo_input["crest_bin"]) != crest_bin:
            crest_bin = Path(avo_input["crest_bin"])
            config["crest_bin"] = str(crest_bin)
            with open(config_file, "w", encoding="utf-8") as config_path:
                json.dump(config, config_path)

        # First setup command to be passed
        charge = avo_input["charge"]
        # "Spin" passed by Avogadro is actually muliplicity so convert to n(unpaired e-)
        spin = avo_input["spin"] - 1
        command = [crest_bin, xyz_path, "--xnam", xtb_bin, "--chrg", str(charge), "--uhf", str(spin)]
        if avo_input["hess"]:
            command.extend(["--prop", "hess"])
        # crest takes energies in kcal so convert if provided in kJ (default)
        if config["energy_units"] == "kJ/mol":
            ewin_kcal = avo_input["ewin"] / 4.184
        else:
            ewin_kcal = avo_input["ewin"]
        command.extend(["--ewin", str(ewin_kcal)])
        if avo_input["solvent"] != "none":
            command.extend(["--alpb", avo_input["solvent"]])

        # Run calculation using formatted command and xyz file
        conformers_path = run_crest(
            command,
            xyz_path
            )

        # Format everything appropriately for Avogadro
        # Start by passing back the original cjson, then add changes
        result = {"moleculeFormat": "cjson", "cjson": avo_input["cjson"]}

        # Catch errors in crest execution (to do)
        #except Exception as ex:
            #print(str(ex))
        #if (error condition):
            #result["message"] = "Error message"
            # Pass back to Avogadro
            #print(json.dumps(result))
            #break

        # Make sure the list of lists is already in place in the cjson
        result["cjson"]["atoms"]["coords"]["3dSets"] = []
        # And the container for the conformer energies
        result["cjson"]["properties"]["energies"] = []

        # The geometries are contained in a multi-structure file
        # Read line by line and add manually to cjson style, splitting by conformer
        n_atoms = int(avo_input["xyz"].split()[0])
        with open(conformers_path, encoding="utf-8") as conf_file:
            structure_number = -1
            while True:
                line = conf_file.readline().strip()
                if line == "":
                    # End of file
                    break
                elif line.split()[0] == str(n_atoms):
                    # Move to next element of 3dSet
                    structure_number += 1
                    # Add an empty list to contain the coordinates
                    result["cjson"]["atoms"]["coords"]["3dSets"].append([])
                    continue
                elif line.split()[0][0] == "-":
                    # This is an energy
                    E_conf = float(line.split()[0])
                    # Add to list of energies
                    result["cjson"]["properties"]["energies"].append(E_conf)
                else:
                    # This is an actual atom!
                    xyz = [float(x) for x in line.split()[1:]]
                    # Add to list of coordinates at appropriate index of 3dSets
                    result["cjson"]["atoms"]["coords"]["3dSets"][structure_number].extend(xyz)

        # Save result
        with open(calc_dir / "result.cjson", "w", encoding="utf-8") as save_file:
            json.dump(result["cjson"], save_file, indent=2)

        # If user specified a save location, copy calculation directory to there
        if Path(avo_input["save_dir"]) != calc_dir:
            copytree(calc_dir, Path(avo_input["save_dir"]), dirs_exist_ok=True)

        # Pass back to Avogadro
        print(json.dumps(result))
