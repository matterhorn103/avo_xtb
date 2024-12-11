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
        print("Frequencies")
    if args.menu_path:
        print("Extensions|Semi-Empirical QM (xTB){870}")

    if args.run_command:
        # Read input from Avogadro
        avo_input = json.loads(sys.stdin.read())
        # Extract the coords
        geom = easyxtb.Geometry.from_cjson(avo_input["cjson"])

        # Run calculation; returns set of frequency data
        logger.debug("avo_xtb is requesting a frequency calculation")
        freqs = easyxtb.calculate.frequencies(
            geom,
            options=easyxtb.config["xtb_opts"],
        )

        freq_cjson = easyxtb.convert.freq_to_cjson(freqs)

        # Start by passing back the original cjson, then add changes
        output = {"moleculeFormat": "cjson", "cjson": avo_input["cjson"].copy()}
        output["cjson"]["vibrations"] = freq_cjson["vibrations"]

        # Inform user if there are negative frequencies
        if freqs[0]["frequency"] < 0:
            output["message"] = (
                "At least one negative frequency found!\n"
                + "This is not a minimum on the potential energy surface.\n"
                + "You should reoptimize the geometry.\n"
                + "This can be avoided in future by using the Opt + Freq method."
            )

        # Save result
        with open(easyxtb.TEMP_DIR / "result.cjson", "w", encoding="utf-8") as save_file:
            json.dump(output["cjson"], save_file, indent=2)
        
        # Pass back to Avogadro
        print(json.dumps(output))
        logger.debug(f"The following dictionary was passed back to Avogadro: {output}")
