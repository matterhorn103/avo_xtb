# Copyright (c) 2023-2024, Matthew J. Milner
# This file is part of avo_xtb which is released under the BSD 3-Clause License.
# See LICENSE or go to https://opensource.org/license/BSD-3-clause for full details.

import argparse
import json
import sys
from pathlib import Path
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
        print("Energy")
    if args.menu_path:
        print("Extensions|Semi-empirical (xtb){890}")

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
        # Extract the coords
        geom = py_xtb.Geometry.from_xyz(avo_input["xyz"].split("\n"))
        #xyz_path = Path(py_xtb.calc_dir) / "input.xyz"
        #with open(xyz_path, "w", encoding="utf-8") as xyz_file:
        #    xyz_file.write(str(geom))

        # Run calculation; returns energy as float in hartree
        energy_hartree = py_xtb.calc.energy(
            geom,
            charge=avo_input["charge"],
            multiplicity=avo_input["spin"],
            solvation=py_xtb.config["solvent"],
            method=py_xtb.config["method"],
        )
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
