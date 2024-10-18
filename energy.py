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
        print("Energy")
    if args.menu_path:
        print("Extensions|Semi-empirical (xtb){890}")

    if args.run_command:

        # Read input from Avogadro
        avo_input = json.loads(sys.stdin.read())
        # Extract the coords
        geom = py_xtb.Geometry.from_xyz(avo_input["xyz"].split("\n"))

        # Run calculation; returns energy as float in hartree
        logger.debug("avo_xtb is requesting a single point energy calculation")
        energy_hartree = py_xtb.calc.energy(
            geom,
            charge=avo_input["charge"],
            multiplicity=avo_input["spin"],
            solvation=py_xtb.config["solvent"],
            method=py_xtb.config["method"],
        )
        # If an energy couldn't be parsed, will return None, so have to allow for that
        if energy_hartree is None:
            # Seems like a reasonable placeholder that should be obviously incorrect to
            # anyone
            energy_hartree = 0.0
        # Convert energy to eV for Avogadro, other units for users
        energies = py_xtb.convert.convert_energy(energy_hartree, "hartree")
        # Format everything appropriately for Avogadro
        # Start by passing back the original cjson, then add changes
        result = {"moleculeFormat": "cjson", "cjson": avo_input["cjson"]}
        # Currently Avogadro ignores the energy result
        result["message"] = (
            f"Energy from GFN{py_xtb.config['method']}-xTB:\n"
            + f"{str(round(energy_hartree, 7))} hartree\n"
            + f"{str(round(energies['eV'], 7))} eV\n"
            + f"{str(round(energies['kJ'], 7))} kJ/mol\n"
            + f"{str(round(energies['kcal'], 7))} kcal/mol\n"
        )
        result["cjson"]["properties"]["totalEnergy"] = str(round(energies["eV"], 7))
        # Pass back to Avogadro
        print(json.dumps(result))
        logger.debug(f"The following dictionary was passed back to Avogadro: {result}")
