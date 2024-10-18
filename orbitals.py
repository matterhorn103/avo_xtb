# Copyright (c) 2023-2024, Matthew J. Milner
# This file is part of avo_xtb which is released under the BSD 3-Clause License.
# See LICENSE or go to https://opensource.org/license/BSD-3-clause for full details.

import argparse
import json
import logging
import sys

from support import py_xtb


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

    # Disable if xtb missing
    if py_xtb.XTB_BIN is None:
        quit()

    if args.print_options:
        options = {"inputMoleculeFormat": "xyz"}
        print(json.dumps(options))
    if args.display_name:
        print("Orbitals")
    if args.menu_path:
        print("Extensions|Semi-empirical (xtb){830}")

    if args.run_command:

        # Read input from Avogadro
        avo_input = json.loads(sys.stdin.read())
        # Extract the coords
        geom = py_xtb.Geometry.from_xyz(avo_input["xyz"].split("\n"))

        # Run calculation; returns Molden output file as string
        logger.debug("avo_xtb is requesting a molecular orbitals calculation")
        molden_string = py_xtb.calc.orbitals(
            geom,
            charge=avo_input["charge"],
            multiplicity=avo_input["spin"],
            solvation=py_xtb.config["solvent"],
            method=py_xtb.config["method"],
        )

        # Format everything appropriately for Avogadro
        # Just pass orbitals file with instruction to read only properties
        result = {
            "readProperties": True,
            "moleculeFormat": "molden",
            "molden": molden_string,
        }
        # As it stands, this means any other properties will be wiped
        # If there were e.g. frequencies in the original cjson, notify the user
        if "vibrations" in avo_input["cjson"]:
            result["message"] = (
                "Calculation complete!\n"
                "The vibrational frequencies may have been lost in this process.\n"
                "Please recalculate them if they are missing and still desired.\n"
            )
        else:
            result["message"] = "Calculation complete!"

        # Save result
        with open(py_xtb.TEMP_DIR / "result.molden", "w", encoding="utf-8") as save_file:
            json.dump(result, save_file, indent=2)

        # Pass back to Avogadro
        print(json.dumps(result))
        logger.debug(f"The following dictionary was passed back to Avogadro: {result}")
