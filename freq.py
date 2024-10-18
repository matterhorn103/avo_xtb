# Copyright (c) 2023-2024, Matthew J. Milner
# This file is part of avo_xtb which is released under the BSD 3-Clause License.
# See LICENSE or go to https://opensource.org/license/BSD-3-clause for full details.

import argparse
import json
import sys

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

    # Disable if xtb missing
    if py_xtb.XTB_BIN is None:
        quit()

    if args.print_options:
        options = {"inputMoleculeFormat": "xyz"}
        print(json.dumps(options))
    if args.display_name:
        print("Frequencies")
    if args.menu_path:
        print("Extensions|Semi-empirical (xtb){870}")

    if args.run_command:

        # Read input from Avogadro
        avo_input = json.loads(sys.stdin.read())
        # Extract the coords
        geom = py_xtb.Geometry.from_xyz(avo_input["xyz"].split("\n"))

        # Run calculation; returns set of frequency data
        freqs = py_xtb.calc.frequencies(
            geom,
            charge=avo_input["charge"],
            multiplicity=avo_input["spin"],
            solvation=py_xtb.config["solvent"],
            method=py_xtb.config["method"],
        )

        freq_cjson = py_xtb.convert.freq_to_cjson(freqs)

        # Start by passing back the original cjson, then add changes
        result = {"moleculeFormat": "cjson", "cjson": avo_input["cjson"]}
        result["cjson"]["vibrations"] = freq_cjson["vibrations"]

        # Inform user if there are negative frequencies
        if freqs[0]["frequency"] < 0:
            result["message"] = (
                "At least one negative frequency found!\n"
                + "This is not a minimum on the potential energy surface.\n"
                + "You should reoptimize the geometry.\n"
                + "This can be avoided in future by using the Opt + Freq method."
            )

        # Save result
        with open(py_xtb.TEMP_DIR / "result.cjson", "w", encoding="utf-8") as save_file:
            json.dump(result["cjson"], save_file, indent=2)
        
        # Pass back to Avogadro
        print(json.dumps(result))
