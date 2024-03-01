# Copyright (c) 2023-2024, Matthew J. Milner
# This file is part of avo_xtb which is released under the BSD 3-Clause License.
# See LICENSE or go to https://opensource.org/license/BSD-3-clause for full details.

import argparse
import json
import sys
from shutil import rmtree
from pathlib import Path

from config import config, calc_dir
from run import run_xtb


def orbitals(
        geom_file: Path,
        charge: int = 0,
        multiplicity: int = 1,
        solvation: str | None = None,
        method: int = 2,
        ) -> Path:

    """Calculate molecular orbitals for given geometry, return file in Molden format."""
    spin = multiplicity - 1
    # Just do a single point calculation but pass molden option to get orbital printout
    command = ["xtb", geom_file, "--molden", "--chrg", str(charge), "--uhf", str(spin), "--gfn", str(method)]
    # Add solvation if requested
    if solvation is not None:
        command.extend(["--alpb", solvation])
    # Run xtb from command line
    calc, out_file, energy = run_xtb(command, geom_file)

    # Return path to molden file
    return geom_file.with_name("molden.input")


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
        print("Orbitals")
    if args.menu_path:
        print("Extensions|Semi-empirical (xtb){830}")

    if args.run_command:
        # Remove results of last calculation
        if calc_dir.exists():
            for x in calc_dir.iterdir():
                if x.is_file():
                    x.unlink()
                elif x.is_dir():
                    rmtree(x)

        # Read input from Avogadro
        avo_input = json.loads(sys.stdin.read())
        # Extract the coords and write to file for use as xtb input
        geom = avo_input["xyz"]
        xyz_path = calc_dir / "input.xyz"
        with open(xyz_path, "w", encoding="utf-8") as xyz_file:
            xyz_file.write(str(geom))

        # Run calculation using xyz file
        result_path = orbitals(
            xyz_path,
            charge=avo_input["charge"],
            multiplicity=avo_input["spin"],
            solvation=config["solvent"],
            method=config["method"],
            )

        # Get molden file as string
        with open(result_path, encoding="utf-8") as molden_file:
            molden_string = molden_file.read()
        # Format everything appropriately for Avogadro
        # Just pass orbitals file with instruction to read only properties
        result = {
            "readProperties": True,
            "moleculeFormat": "molden",
            "molden": molden_string,
        }
        # As it stands, this means any other properties will be wiped
        # If there were e.g. frequencies in the original cjson, notify the user
        if "vibrations" in avo_input["cjson"]:
            result["message"] = (
                "Calculation complete!\n"
                "The vibrational frequencies may have been lost in this process.\n"
                "Please recalculate them if they are missing and still desired.\n"
            )
        else:
            result["message"] = "Calculation complete!"

        # Pass back to Avogadro
        print(json.dumps(result))
