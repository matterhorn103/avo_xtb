# Copyright (c) 2023-2024, Matthew J. Milner
# This file is part of avo_xtb which is released under the BSD 3-Clause License.
# See LICENSE or go to https://opensource.org/license/BSD-3-clause for full details.

import argparse
import json
import sys
from shutil import rmtree

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
        print("Optimize")
    if args.menu_path:
        print("Extensions|Semi-empirical (xtb){880}")

    if args.run_command:

        # Read input from Avogadro
        avo_input = json.loads(sys.stdin.read())
        # Extract the coords
        geom = py_xtb.Geometry.from_xyz(avo_input["xyz"].split("\n"))

        # Run calculation; returns optimized geometry as well as Calculation object
        opt_geom, calc = py_xtb.calc.optimize(
            geom,
            charge=avo_input["charge"],
            multiplicity=avo_input["spin"],
            solvation=py_xtb.config["solvent"],
            method=py_xtb.config["method"],
            level=py_xtb.config["opt_lvl"],
            return_calc=True,
        )

        # Convert geometry
        cjson_geom = opt_geom.to_cjson()
        # Check for convergence
        # TODO
        # Will need to look for "FAILED TO CONVERGE"
        # Convert energy for Avogadro
        energies = py_xtb.convert.convert_energy(calc.energy, "hartree")
        # Format everything appropriately for Avogadro
        # Start by passing back the original cjson, then add changes
        result = {"moleculeFormat": "cjson", "cjson": avo_input["cjson"]}
        result["cjson"]["atoms"]["coords"] = cjson_geom["atoms"]["coords"]
        result["cjson"]["properties"]["totalEnergy"] = str(round(energies["eV"], 7))

        # If the cjson contained frequencies or orbitals, remove them as they are no longer physical
        for field in ["vibrations", "basisSet", "orbitals", "cube"]:
            if field in result["cjson"]:
                del result["cjson"][field]

        # Save result
        with open(py_xtb.CALC_DIR / "result.cjson", "w", encoding="utf-8") as save_file:
            json.dump(result["cjson"], save_file, indent=2)
        # Pass back to Avogadro
        print(json.dumps(result))
