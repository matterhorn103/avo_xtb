"""
avo_xtb
A full-featured interface to xtb in Avogadro 2.
Copyright (c) 2023, Matthew J. Milner

BSD 3-Clause License

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import argparse
import json
import sys
from pathlib import Path
from shutil import rmtree

from config import config, calc_dir, xtb_bin
import convert
import obabel_convert
from run import run_xtb


def opt_freq(
        geom_file: Path,
        charge: int = 0,
        multiplicity: int = 1,
        solvation: str | None = None,
        method: int = 2,
        level: str = "normal",
        ) -> tuple[Path, Path, float]:
    """Optimize geometry then calculate vibrational frequencies. Distort and reoptimize if negative frequency detected."""
    spin = multiplicity - 1
    command = ["xtb", geom_file, "--ohess", level, "--chrg", str(charge), "--uhf", str(spin), "--gfn", str(method)]
    # Add solvation if requested
    if solvation is not None:
        command.extend(["--alpb", solvation])
    # Run xtb from command line
    calc, out_file, energy = run_xtb(command, geom_file)

    # Make sure the first calculation has finished
    # (How?)

    # Check for distorted geometry
    # (Generated automatically by xtb if result had negative frequency)
    # If so, rerun
    distorted_geom = geom_file.with_stem("xtbhess")
    if distorted_geom.exists():
        calc, out_file, energy = run_xtb(command, distorted_geom)

    # Return the path of the Gaussian file generated
    return geom_file.with_stem("xtbopt"), geom_file.with_name("g98.out"), energy


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
        out_geom, out_freq, energy = opt_freq(
            xyz_path,
            charge=avo_input["charge"],
            multiplicity=avo_input["spin"],
            solvation=config["solvent"],
            method=config["method"],
            level=config["level"],
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
        # TO DO
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
            result["message"] = ("At least one negative frequency found!\n"
                                 "This is not a minimum on the potential energy surface.\n"
                                 "You should reoptimize the geometry.")

        # Save result
        with open(calc_dir / "result.cjson", "w", encoding="utf-8") as save_file:
            json.dump(result["cjson"], save_file, indent=2)
        # Pass back to Avogadro
        print(json.dumps(result))