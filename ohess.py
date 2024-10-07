# Copyright (c) 2023-2024, Matthew J. Milner
# This file is part of avo_xtb which is released under the BSD 3-Clause License.
# See LICENSE or go to https://opensource.org/license/BSD-3-clause for full details.

import argparse
import json
import sys
from pathlib import Path
from shutil import rmtree

from py_xtb import config, calc_dir, convert, calc
import obabel_convert


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
        print("Opt + Freq")
    if args.menu_path:
        print("Extensions|Semi-empirical (xtb){860}")

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
        out_geom, out_freq, energy = calc.opt_freq(
            xyz_path,
            charge=avo_input["charge"],
            multiplicity=avo_input["spin"],
            solvation=config["solvent"],
            method=config["method"],
            level=config["opt_lvl"],
        )

        # Convert frequencies
        # Currently Avogadro fails to convert the g98 file to cjson itself
        # So we have to convert output in g98 format to cjson ourselves
        freq_cjson_path = obabel_convert.g98_to_cjson(out_freq)
        # Open the cjson
        with open(freq_cjson_path, encoding="utf-8") as result_cjson:
            freq_cjson = json.load(result_cjson)

        # Convert geometry
        geom_cjson_path = obabel_convert.xyz_to_cjson(out_geom)
        # Open the cjson
        with open(geom_cjson_path, encoding="utf-8") as result_cjson:
            geom_cjson = json.load(result_cjson)
        # Check for convergence
        # TODO
        # Will need to look for "FAILED TO CONVERGE"

        # Convert energy for Avogadro
        energies = convert.convert_energy(energy, "hartree")

        # Format appropriately for Avogadro
        # Start by passing back the original cjson, then add changes
        result = {"moleculeFormat": "cjson", "cjson": avo_input["cjson"]}
        # Add data from calculation
        result["cjson"]["vibrations"] = freq_cjson["vibrations"]
        result["cjson"]["atoms"]["coords"] = geom_cjson["atoms"]["coords"]
        result["cjson"]["properties"]["totalEnergy"] = str(round(energies["eV"], 7))
        # xtb no longer gives Raman intensities but does write them as all 0
        # If passed on to the user this is misleading so remove them
        if "ramanIntensities" in result["cjson"]["vibrations"]:
            del result["cjson"]["vibrations"]["ramanIntensities"]
        # If the cjson contained orbitals, remove them as they are no longer physical
        for field in ["basisSet", "orbitals", "cube"]:
            if field in result["cjson"]:
                del result["cjson"][field]

        # Inform user if there are negative frequencies
        if float(freq_cjson["vibrations"]["frequencies"][0]) < 0:
            result["message"] = (
                "At least one negative frequency found!\n"
                + "This is not a minimum on the potential energy surface.\n"
                + "You should reoptimize the geometry."
            )

        # Save result
        with open(calc_dir / "result.cjson", "w", encoding="utf-8") as save_file:
            json.dump(result["cjson"], save_file, indent=2)
        # Pass back to Avogadro
        print(json.dumps(result))
