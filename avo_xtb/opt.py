# SPDX-FileCopyrightText: 2024 Matthew J. Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

import argparse
import json
import logging
import sys

from support import easyxtb


logger = logging.getLogger(__name__)


def cleanup_after_opt(cjson: dict) -> dict:
    """Returns a copy of a cjson dict minus any data that is no longer meaningful after
    a geometry change."""

    output = cjson.copy()

    # Frequencies and orbitals
    for field in ["vibrations", "basisSet", "orbitals", "cube"]:
        if field in output:
            del output[field]
    # Atomic charges
    if "formalCharges" in output["atoms"]:
        del output["atoms"]["formalCharges"]
    if "partialCharges" in output["atoms"]:
        del output["atoms"]["partialCharges"]
    
    return output


def opt(avo_input: dict) -> dict:
    # Extract the coords
    geom = easyxtb.Geometry.from_cjson(avo_input["cjson"])

    # Run calculation
    logger.debug("avo_xtb is requesting a geometry optimization")
    calc = easyxtb.Calculation.opt(
        geom,
        options=easyxtb.config["xtb_opts"],
    )
    calc.run()

    # Convert geometry to cjson
    geom_cjson = calc.output_geometry.to_cjson()

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
    output["cjson"]["atoms"]["coords"] = geom_cjson["atoms"]["coords"]
    output["cjson"]["properties"]["totalEnergy"] = round(energies["eV"], 7)
    # Partial charges if present
    if hasattr(calc, "partial_charges"):
        output["cjson"]["atoms"]["partialCharges"] = calc.partial_charges

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
    if easyxtb.XTB.path is None:
        quit()

    if args.print_options:
        options = {"inputMoleculeFormat": "xyz"}
        print(json.dumps(options))
        
    if args.display_name:
        print("Optimize")

    if args.menu_path:
        print("Extensions|Semi-Empirical QM (xTB){880}")

    if args.run_command:
        # Read input from Avogadro
        avo_input = json.loads(sys.stdin.read())
        output = opt(avo_input)
        # Pass back to Avogadro
        print(json.dumps(output))
        logger.debug(f"The following dictionary was passed back to Avogadro: {output}")
