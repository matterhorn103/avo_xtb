# Copyright (c) 2023-2024, Matthew J. Milner
# This file is part of avo_xtb which is released under the BSD 3-Clause License.
# See LICENSE or go to https://opensource.org/license/BSD-3-clause for full details.

import argparse
import json
import sys
from pathlib import Path
from shutil import rmtree, copytree

from support import py_xtb



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--print-options", action="store_true")
    parser.add_argument("--run-command", action="store_true")
    parser.add_argument("--display-name", action="store_true")
    parser.add_argument("--lang", nargs="?", default="en")
    parser.add_argument("--menu-path", action="store_true")
    args = parser.parse_args()

    # Disable if xtb and crest missing
    if py_xtb.XTB_BIN is None or py_xtb.CREST_BIN is None:
        quit()

    if args.print_options:
        options = {
            "inputMoleculeFormat": "xyz",
            "userOptions": {
                "crest_bin": {
                    "type": "string",
                    "label": "Location of the CREST binary",
                    "default": str(py_xtb.CREST_BIN),
                    "order": 1.0,
                },
                "save_dir": {
                    "type": "string",
                    "label": "Save results in",
                    "default": str(py_xtb.calc_dir),
                    "order": 2.0,
                },
                # "Number of threads": {
                #    "type": "integer",
                #    #"label": "Number of cores",
                #    "minimum": 1,
                #    "default": 1,
                #    "order": 3.0
                #    },
                # "Memory per core": {
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
                    "order": 9.0,
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
                        "water",
                    ],
                    "default": 0,
                    "order": 6.0,
                },
                "ewin": {
                    "type": "integer",
                    "label": "Keep all conformers within",
                    "default": 25,
                    "minimum": 1,
                    "maximum": 1000,
                    "suffix": " kJ/mol",
                    "order": 7.0,
                },
                "hess": {
                    "type": "boolean",
                    "label": "Calculate frequencies for conformers\nand re-weight ensemble on free energies",
                    "default": False,
                    "order": 8.0,
                },
            },
        }
        # Display energy in kcal if user has insisted on it
        if py_xtb.config["energy_units"] == "kcal/mol":
            options["userOptions"]["ewin"]["default"] = 6
            options["userOptions"]["ewin"]["suffix"] = " kcal/mol"
        # Make solvation default if found in user config
        if py_xtb.config["solvent"] is not None:
            options["userOptions"]["solvent"]["default"] = py_xtb.config["solvent"]
        print(json.dumps(options))
    if args.display_name:
        print("Conformers…")
    if args.menu_path:
        print("Extensions|Semi-empirical (xtb){770}")

    if args.run_command:
        # Remove results of last calculation
        if py_xtb.calc_dir.exists():
            for x in py_xtb.calc_dir.iterdir():
                if x.is_file():
                    x.unlink()
                elif x.is_dir():
                    rmtree(x)

        # Read input from Avogadro
        avo_input = json.loads(sys.stdin.read())
        # Extract the coords and write to file for use as xtb input
        geom = avo_input["xyz"]
        xyz_path = py_xtb.calc_dir / "input.xyz"
        with open(xyz_path, "w", encoding="utf-8") as xyz_file:
            xyz_file.write(str(geom))

        # If provided crest path different to that stored, use it and save it
        if Path(avo_input["crest_bin"]) != py_xtb.CREST_BIN:
            crest_bin = Path(avo_input["crest_bin"])
            py_xtb.config["crest_bin"] = str(crest_bin)
            with open(py_xtb.config_file, "w", encoding="utf-8") as config_path:
                json.dump(py_xtb.config, config_path)

        # crest takes energies in kcal so convert if provided in kJ (default)
        if py_xtb.config["energy_units"] == "kJ/mol":
            ewin_kcal = avo_input["ewin"] / 4.184
        else:
            ewin_kcal = avo_input["ewin"]
        
        # Convert "none" string to Python None
        if avo_input["solvent"] == "none":
            solvation = None
        else:
            solvation = avo_input["solvent"]

        # Run calculation using xyz file
        conformers_path = py_xtb.calc.conformers(
            xyz_path,
            charge=avo_input["charge"],
            multiplicity=avo_input["spin"],
            solvation=solvation,
            ewin=ewin_kcal,
            hess=avo_input["hess"],
        )

        # Format everything appropriately for Avogadro
        # Start by passing back the original cjson, then add changes
        result = {"moleculeFormat": "cjson", "cjson": avo_input["cjson"]}

        # Catch errors in crest execution
        # TODO

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
                    result["cjson"]["atoms"]["coords"]["3dSets"][
                        structure_number
                    ].extend(xyz)

        # Save result
        with open(py_xtb.calc_dir / "result.cjson", "w", encoding="utf-8") as save_file:
            json.dump(result["cjson"], save_file, indent=2)

        # If user specified a save location, copy calculation directory to there
        if not (
            avo_input["save_dir"] in ["", None]
            or Path(avo_input["save_dir"]) == py_xtb.calc_dir
        ):
            copytree(py_xtb.calc_dir, Path(avo_input["save_dir"]), dirs_exist_ok=True)

        # Pass back to Avogadro
        print(json.dumps(result))
