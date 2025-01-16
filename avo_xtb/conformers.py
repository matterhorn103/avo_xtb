# SPDX-FileCopyrightText: 2024 Matthew J. Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

import argparse
import json
import logging
import sys

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
    if easyxtb.XTB.path is None or easyxtb.CREST.path is None:
        quit()

    if args.print_options:
        options = {
            "userOptions": {
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
                "help": {
                    "type": "text",
                    "label": "For help see",
                    "default": "https://crest-lab.github.io/crest-docs/",
                    "order": 9.0,
                },
            },
        }
        # Display energy in kcal if user has insisted on it
        if easyxtb.config["energy_units"] == "kcal/mol":
            options["userOptions"]["ewin"]["default"] = 6
            options["userOptions"]["ewin"]["suffix"] = " kcal/mol"
        print(json.dumps(options))
    if args.display_name:
        print("Conformers…")
    if args.menu_path:
        print("Extensions|Semi-Empirical QM (xTB){770}")

    if args.run_command:
        # Read input from Avogadro
        avo_input = json.loads(sys.stdin.read())
        # Extract the coords
        geom = easyxtb.Geometry.from_cjson(avo_input["cjson"])

        # crest takes energies in kcal so convert if provided in kJ (default)
        if easyxtb.config["energy_units"] == "kJ/mol":
            ewin_kcal = avo_input["ewin"] / 4.184
        else:
            ewin_kcal = avo_input["ewin"]

        # Run calculation
        calc = easyxtb.Calculation.v3(
            geom,
            ewin=ewin_kcal,
            hess=avo_input["hess"],
            options=easyxtb.config["crest_opts"],
        )
        calc.run()

        best_cjson = calc.output_geometry.to_cjson()
        conformer_cjson = easyxtb.convert.conf_to_cjson(calc.conformers)

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

        # Pass back to Avogadro
        print(json.dumps(output))
        logger.debug(f"The following dictionary was passed back to Avogadro: {output}")
