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

    if args.print_options:
        options = {"inputMoleculeFormat": "xyz"}
        print(json.dumps(options))
    if args.display_name:
        print("Optimize")
    if args.menu_path:
        print("Extensions|Semi-empirical (xtb){880}")

    if args.run_command:
        # Remove results of last calculation
        if py_xtb.calc_dir.exists():
            for x in py_xtb.calc_dir.iterdir():
                if x.is_file():
                    x.unlink()
                elif x.is_dir():
                    rmtree(x)

        # Read input from Avogadro
        avo_input = json.loads(sys.stdin.read())
        # Extract the coords and write to file for use as xtb input
        geom = avo_input["xyz"]
        xyz_path =py_xtb.calc_dir / "input.xyz"
        with open(xyz_path, "w", encoding="utf-8") as xyz_file:
            xyz_file.write(str(geom))

        # Run calculation using xyz file
        result_path, energy = py_xtb.calc.optimize(
            xyz_path,
            charge=avo_input["charge"],
            multiplicity=avo_input["spin"],
            solvation=py_xtb.config["solvent"],
            method=py_xtb.config["method"],
            level=py_xtb.config["opt_lvl"],
        )

        # Read the xyz file
        with open(result_path.with_name("xtbopt.xyz"), encoding="utf-8") as result_xyz:
            xyz = result_xyz.read().split("\n")
        # Convert geometry
        cjson_geom = py_xtb.convert.xyz_to_cjson(xyz_lines=xyz)
        # Check for convergence
        # TODO
        # Will need to look for "FAILED TO CONVERGE"
        # Convert energy for Avogadro
        energies = py_xtb.convert.convert_energy(energy, "hartree")
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
        with open(py_xtb.calc_dir / "result.cjson", "w", encoding="utf-8") as save_file:
            json.dump(result["cjson"], save_file, indent=2)
        # Pass back to Avogadro
        print(json.dumps(result))
