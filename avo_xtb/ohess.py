# SPDX-FileCopyrightText: 2024 Matthew J. Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

import argparse
import json
import logging
import sys

from support import easyxtb
from opt import cleanup_after_opt


logger = logging.getLogger(__name__)


def ohess(avo_input: dict) -> dict:
    # Extract the coords
    geom = easyxtb.Geometry.from_cjson(avo_input["cjson"])

    # Run calculation; returns path to Gaussian file containing frequencies
    logger.debug("avo_xtb is requesting an opt+freq calculation")
    opt_geom, freqs, calc = easyxtb.calculate.opt_freq(
        geom,
        options=easyxtb.config["xtb_opts"],
        return_calc=True,
    )

    # Convert geometry and frequencies to cjson
    geom_cjson = opt_geom.to_cjson()
    freq_cjson = easyxtb.convert.freq_to_cjson(freqs)

    # Check for convergence
    # TODO
    # Will need to look for "FAILED TO CONVERGE"

    # Get energy for Avogadro
    energies = easyxtb.convert.convert_energy(calc.energy, "hartree")

    # Format everything appropriately for Avogadro
    # Start from the original cjson
    output = {"moleculeFormat": "cjson", "cjson": avo_input["cjson"].copy()}

    # Remove anything that is now unphysical after the optimization
    output["cjson"] = cleanup_after_opt(output["cjson"])

    # Add data from calculation
    output["cjson"]["vibrations"] = freq_cjson["vibrations"]
    output["cjson"]["atoms"]["coords"] = geom_cjson["atoms"]["coords"]
    output["cjson"]["properties"]["totalEnergy"] = round(energies["eV"], 7)
    # Partial charges if present
    if hasattr(calc, "partial_charges"):
        output["cjson"]["atoms"]["partialCharges"] = calc.partial_charges

    # Inform user if there are negative frequencies
    if freqs[0]["frequency"] < 0:
        output["message"] = (
            "At least one negative frequency found!\n"
            + "This is not a minimum on the potential energy surface.\n"
            + "You should reoptimize the geometry."
        )

    # Save result
    with open(easyxtb.TEMP_DIR / "result.cjson", "w", encoding="utf-8") as save_file:
        json.dump(output["cjson"], save_file, indent=2)

    return output


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
        print("Opt + Freq")
    if args.menu_path:
        print("Extensions|Semi-Empirical QM (xTB){860}")

    if args.run_command:
        # Read input from Avogadro
        avo_input = json.loads(sys.stdin.read())
        output = ohess(avo_input)
        # Pass back to Avogadro
        print(json.dumps(output))
        logger.debug(f"The following dictionary was passed back to Avogadro: {output}")
