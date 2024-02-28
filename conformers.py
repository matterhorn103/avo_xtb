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

from config import config, calc_dir, xtb_bin, crest_bin, config_file
from run import run_crest

# Disable if xtb and crest missing
if xtb_bin is None or crest_bin is None:
    quit()


def conformers(
        geom_file: Path,
        charge: int = 0,
        multiplicity: int = 1,
        solvation: str | None = None,
        ewin: int | float = 6,
        hess: bool = False,
        ) -> Path:
    """Simulate a conformer ensemble and return multi-geometry xyz file.
    
    All conformers within <ewin> kcal/mol are kept.
    If hess=True, vibrational frequencies are calculated and the conformers reordered by Gibbs energy.
    """
    unpaired_e = multiplicity - 1
    command = [crest_bin, geom_file, "--xnam", xtb_bin, "--chrg", str(charge), "--uhf", str(unpaired_e), "--ewin", str(ewin)]
    # Add solvation if requested
    if solvation is not None:
        command.append("--alpb")
        command.append(solvation)
    if hess:
        command.extend(["--prop", "hess"])

    # Run crest from command line
    calc, out_file = run_crest(command, geom_file)

    return geom_file.with_stem("crest_conformers")


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
                    "label": "Location of the CREST binary",
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
        print("Extensions|Semi-empirical (xtb){770}")

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

        # crest takes energies in kcal so convert if provided in kJ (default)
        if config["energy_units"] == "kJ/mol":
            ewin_kcal = avo_input["ewin"] / 4.184
        else:
            ewin_kcal = avo_input["ewin"]

        # Run calculation using xyz file
        conformers_path = conformers(
            xyz_path,
            charge=avo_input["charge"],
            multiplicity=avo_input["spin"],
            solvation=avo_input["solvent"],
            ewin=ewin_kcal,
            hess=avo_input["hess"]
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
        if not (avo_input["save_dir"] in ["", None] or Path(avo_input["save_dir"]) == calc_dir):
            copytree(calc_dir, Path(avo_input["save_dir"]), dirs_exist_ok=True)

        # Pass back to Avogadro
        print(json.dumps(result))
