# Copyright (c) 2023-2024, Matthew J. Milner
# This file is part of avo_xtb which is released under the BSD 3-Clause License.
# See LICENSE or go to https://opensource.org/license/BSD-3-clause for full details.

import argparse
import json
import sys
from pathlib import Path
from shutil import rmtree

from config import config, calc_dir
import obabel_convert
from run import run_xtb


def frequencies(

        geom_file: Path,
        charge: int = 0,
        multiplicity: int = 1,
        solvation: str | None = None,
        method: int = 2,
        ) -> Path:
    """Calculate vibrational frequencies and return Gaussian 98 format output file."""
    unpaired_e = multiplicity - 1
    command = ["xtb", geom_file, "--hess", "--chrg", str(charge), "--uhf", str(unpaired_e), "--gfn", str(method)]

    # Add solvation if requested
    if solvation is not None:
        command.extend(["--alpb", solvation])
    # Run xtb from command line
    calc, out_file, energy = run_xtb(command, geom_file)

    # Return the path of the Gaussian file generated
    return geom_file.with_name("g98.out")


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
        print("Frequencies")
    if args.menu_path:
        print("Extensions|Semi-empirical (xtb){870}")

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
        xyz_path = Path(calc_dir) / "input.xyz"
        with open(xyz_path, "w", encoding="utf-8") as xyz_file:
            xyz_file.write(str(geom))

        # Run calculation; returns path to Gaussian file containing frequencies
        result_path = frequencies(
            xyz_path,
            charge=avo_input["charge"],
            multiplicity=avo_input["spin"],
            solvation=config["solvent"],
            method=config["method"],
            )

        # Currently Avogadro fails to convert the g98 file to cjson itself
        # So we have to convert output in g98 format to cjson ourselves
        cjson_path = obabel_convert.g98_to_cjson(result_path)
        # Open the cjson
        with open(cjson_path, encoding="utf-8") as result_cjson:
            freq_cjson = json.load(result_cjson)
        # Format appropriately for Avogadro
        # Start by passing back the original cjson, then add changes
        result = {"moleculeFormat": "cjson", "cjson": avo_input["cjson"]}
        result["cjson"]["vibrations"] = freq_cjson["vibrations"]
        # xtb no longer gives Raman intensities but does write them as all 0
        # If passed on to the user this is misleading so remove them
        if "ramanIntensities" in result["cjson"]["vibrations"]:
            del result["cjson"]["vibrations"]["ramanIntensities"]

        # Inform user if there are negative frequencies
        if float(freq_cjson["vibrations"]["frequencies"][0]) < 0:
            result["message"] = (
                "At least one negative frequency found!\n"
                "This is not a minimum on the potential energy surface.\n"
                "You should reoptimize the geometry.\n"
                "This can be avoided in future by using the Opt + Freq method."
            )

        # Save result
        with open(calc_dir / "result.cjson", "w", encoding="utf-8") as save_file:
            json.dump(result["cjson"], save_file, indent=2)
        # Pass back to Avogadro
        print(json.dumps(result))
