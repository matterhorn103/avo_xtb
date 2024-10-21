# SPDX-FileCopyrightText: 2024 Matthew J. Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

import argparse
import json
import logging
import sys

from support import py_xtb
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

    # Disable if xtb missing
    if py_xtb.XTB_BIN is None:
        quit()

    if args.print_options:
        options = {"inputMoleculeFormat": "xyz"}
        print(json.dumps(options))
    if args.display_name:
        print("Opt + Freq")
    if args.menu_path:
        print("Extensions|Semi-empirical (xtb){860}")

    if args.run_command:

        # Read input from Avogadro
        avo_input = json.loads(sys.stdin.read())
        # Extract the coords
        geom = py_xtb.Geometry.from_xyz(avo_input["xyz"].split("\n"))

        # Run calculation; returns path to Gaussian file containing frequencies
        logger.debug("avo_xtb is requesting an opt+freq calculation")
        opt_geom, freqs, calc = py_xtb.calc.opt_freq(
            geom,
            charge=avo_input["charge"],
            multiplicity=avo_input["spin"],
            solvation=py_xtb.config["solvent"],
            method=py_xtb.config["method"],
            level=py_xtb.config["opt_lvl"],
            return_calc=True,
        )

        # Convert geometry and frequencies to cjson
        geom_cjson = opt_geom.to_cjson()
        freq_cjson = py_xtb.convert.freq_to_cjson(freqs)

        # Check for convergence
        # TODO
        # Will need to look for "FAILED TO CONVERGE"

        # Get energy for Avogadro
        energies = py_xtb.convert.convert_energy(calc.energy, "hartree")

        # Format everything appropriately for Avogadro
        # Start from the original cjson
        result = {"moleculeFormat": "cjson", "cjson": avo_input["cjson"]}

        # Remove anything that is now unphysical after the optimization
        result["cjson"] = cleanup_after_opt(result["cjson"])

        # Add data from calculation
        result["cjson"]["vibrations"] = freq_cjson["vibrations"]
        result["cjson"]["atoms"]["coords"] = geom_cjson["atoms"]["coords"]
        result["cjson"]["properties"]["totalEnergy"] = str(round(energies["eV"], 7))

        # Inform user if there are negative frequencies
        if freqs[0]["frequency"] < 0:
            result["message"] = (
                "At least one negative frequency found!\n"
                + "This is not a minimum on the potential energy surface.\n"
                + "You should reoptimize the geometry."
            )

        # Save result
        with open(py_xtb.TEMP_DIR / "result.cjson", "w", encoding="utf-8") as save_file:
            json.dump(result["cjson"], save_file, indent=2)
        
        # Pass back to Avogadro
        print(json.dumps(result))
        logger.debug(f"The following dictionary was passed back to Avogadro: {result}")
