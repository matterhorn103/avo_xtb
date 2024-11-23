# SPDX-FileCopyrightText: 2024 Matthew J. Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

import argparse
import json
import logging
import sys
from pathlib import Path
from shutil import copytree

from support import easyxtb
from opt import cleanup_after_opt


logger = logging.getLogger(__name__)


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
    if easyxtb.XTB_BIN is None or easyxtb.CREST_BIN is None:
        quit()

    if args.print_options:
        options = {
            "inputMoleculeFormat": "xyz",
            "userOptions": {
                "crest_bin": {
                    "type": "string",
                    "label": "Location of the CREST binary",
                    "default": str(easyxtb.CREST_BIN),
                    "order": 1.0,
                },
                "save_dir": {
                    "type": "string",
                    "label": "Save results in",
                    "default": str(easyxtb.CALC_DIR),
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
        if easyxtb.config["energy_units"] == "kcal/mol":
            options["userOptions"]["ewin"]["default"] = 6
            options["userOptions"]["ewin"]["suffix"] = " kcal/mol"
        # Make solvation default if found in user config
        if easyxtb.config["solvent"] is not None:
            options["userOptions"]["solvent"]["default"] = easyxtb.config["solvent"]
        print(json.dumps(options))
    if args.display_name:
        print("Conformers…")
    if args.menu_path:
        print("Extensions|Semi-empirical (xtb){770}")

    if args.run_command:
        # Read input from Avogadro
        avo_input = json.loads(sys.stdin.read())
        # Extract the coords
        geom = easyxtb.Geometry.from_cjson(avo_input["cjson"])

        # If provided crest path different to that stored, use it and save it
        if Path(avo_input["crest_bin"]) != easyxtb.CREST_BIN:
            crest_bin = Path(avo_input["crest_bin"])
            easyxtb.config["crest_bin"] = str(crest_bin)
            with open(easyxtb.config_file, "w", encoding="utf-8") as config_path:
                json.dump(easyxtb.config, config_path)

        # crest takes energies in kcal so convert if provided in kJ (default)
        if easyxtb.config["energy_units"] == "kJ/mol":
            ewin_kcal = avo_input["ewin"] / 4.184
        else:
            ewin_kcal = avo_input["ewin"]
        
        # Convert "none" string to Python None
        if avo_input["solvent"] == "none":
            solvation = None
        else:
            solvation = avo_input["solvent"]

        # Run calculation; returns set of conformers as well as Calculation object
        conformers, calc = easyxtb.calc.conformers(
            geom,
            solvation=solvation,
            method=2,
            ewin=ewin_kcal,
            hess=avo_input["hess"],
            return_calc=True,
        )

        best_cjson = calc.output_geometry.to_cjson()
        conformer_cjson = easyxtb.convert.conf_to_cjson(conformers)

        # Get energy for Avogadro
        energies = easyxtb.convert.convert_energy(calc.energy, "hartree")

        # Format everything appropriately for Avogadro
        # Start by passing back the original cjson, then add changes
        output = {"moleculeFormat": "cjson", "cjson": avo_input["cjson"].copy()}

        # Catch errors in crest execution
        # TODO

        # Remove anything that is now unphysical after the optimization
        output["cjson"] = cleanup_after_opt(output["cjson"])

        # Add data from calculation
        output["cjson"]["atoms"]["coords"] = best_cjson["atoms"]["coords"]
        output["cjson"]["properties"]["totalEnergy"] = round(energies["eV"], 7)
        output["cjson"]["atoms"]["coords"]["3dSets"] = conformer_cjson["atoms"]["coords"]["3dSets"]
        output["cjson"]["properties"]["energies"] = conformer_cjson["properties"]["energies"]

        # Save result
        with open(easyxtb.TEMP_DIR / "result.cjson", "w", encoding="utf-8") as save_file:
            json.dump(output["cjson"], save_file, indent=2)

        # If user specified a save location, copy calculation directory to there
        if not (
            avo_input["save_dir"] in ["", None]
            or Path(avo_input["save_dir"]) == easyxtb.TEMP_DIR
        ):
            copytree(easyxtb.TEMP_DIR, Path(avo_input["save_dir"]), dirs_exist_ok=True)

        # Pass back to Avogadro
        print(json.dumps(output))
        logger.debug(f"The following dictionary was passed back to Avogadro: {output}")
