# SPDX-FileCopyrightText: 2024 Matthew J. Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

import argparse
import json
import logging
import sys

from support import easyxtb
from protonate import cleanup_after_taut


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

    # Disable if xtb or crest missing
    if easyxtb.XTB_BIN is None or easyxtb.CREST_BIN is None:
        quit()

    if args.print_options:
        options = {"inputMoleculeFormat": "xyz"}
        print(json.dumps(options))
    if args.display_name:
        print("Deprotonate")
    if args.menu_path:
        print("Extensions|Semi-empirical (xtb){730}")

    if args.run_command:
        # Read input from Avogadro
        avo_input = json.loads(sys.stdin.read())
        # Extract the coords
        geom = easyxtb.Geometry.from_cjson(avo_input["cjson"])

        # Run calculation; returns set of tautomers as well as Calculation object
        tautomers, calc = easyxtb.calculate.deprotonate(
            geom,
            solvation=easyxtb.config["solvent"],
            method=easyxtb.config["method"],
            return_calc=True,
        )

        best_cjson = calc.output_geometry.to_cjson()
        tautomer_cjson = easyxtb.convert.taut_to_cjson(tautomers)

        # Get energy for Avogadro
        energies = easyxtb.convert.convert_energy(calc.energy, "hartree")

        # Format everything appropriately for Avogadro
        # Start by passing back a cleaned version of original cjson
        output = {
            "moleculeFormat": "cjson",
            # Remove anything that is now unphysical after the optimization
            "cjson": cleanup_after_taut(avo_input["cjson"]),
        }

        # Add data from calculation
        output["cjson"]["atoms"] = best_cjson["atoms"]
        output["cjson"]["properties"]["totalEnergy"] = round(energies["eV"], 7)
        output["cjson"]["atoms"]["coords"]["3dSets"] = tautomer_cjson["atoms"]["coords"]["3dSets"]
        output["cjson"]["properties"]["energies"] = tautomer_cjson["properties"]["energies"]

        # Make sure to adjust new charge
        output["cjson"]["properties"]["totalCharge"] -= 1

        # Save result
        with open(easyxtb.TEMP_DIR / "result.cjson", "w", encoding="utf-8") as save_file:
            json.dump(output["cjson"], save_file, indent=2)

        # Pass back to Avogadro
        print(json.dumps(output))
        logger.debug(f"The following dictionary was passed back to Avogadro: {output}")
