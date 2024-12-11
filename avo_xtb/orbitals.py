# SPDX-FileCopyrightText: 2024 Matthew J. Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

import argparse
import json
import logging
import sys

from support import easyxtb


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
    if easyxtb.XTB_BIN is None:
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
        geom = easyxtb.Geometry.from_cjson(avo_input["cjson"])

        # Run calculation; returns Molden output file as string
        logger.debug("avo_xtb is requesting a molecular orbitals calculation")
        molden_string = easyxtb.calculate.orbitals(
            geom,
            options=easyxtb.config["xtb_opts"],
        )

        # Format everything appropriately for Avogadro
        # Just pass orbitals file with instruction to read only properties
        output = {
            "readProperties": True,
            "moleculeFormat": "molden",
            "molden": molden_string,
            "cjson": avo_input["cjson"],
        }
        # As it stands, this means any other properties will be wiped
        # If there were e.g. frequencies in the original cjson, notify the user
        if "vibrations" in avo_input["cjson"]:
            output["message"] = (
                "Calculation complete!\n"
                "The vibrational frequencies may have been lost in this process.\n"
                "Please recalculate them if they are missing and still desired.\n"
            )
        else:
            output["message"] = "Calculation complete!"

        # Save result
        with open(easyxtb.TEMP_DIR / "result.molden", "w", encoding="utf-8") as save_file:
            json.dump(output, save_file, indent=2)

        # Pass back to Avogadro
        print(json.dumps(output))
        logger.debug(f"The following dictionary was passed back to Avogadro: {output}")
