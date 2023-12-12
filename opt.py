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
import os
import sys
from pathlib import Path
from shutil import rmtree

from config import config, calc_dir, xtb_bin
import convert
from run import run_xtb


def optimize(geom_file, charge=0, multiplicity=1):
    spin = multiplicity - 1
    command = ["xtb", geom_file, "--opt", "--chrg", str(charge), "--uhf", str(spin)]
    # Add solvation if set globally
    if config["solvent"] is not None:
        command.append("--alpb")
        command.append(config["solvent"])
    # Run xtb from command line
    calc, out_file, energy = run_xtb(command, geom_file)
    # Return path to geometry file with same suffix, along with energy
    return (geom_file.with_stem("xtbopt"), energy)


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
        # Only show menu option if xtb binary was found
        if xtb_bin is not None:
            print("Extensions|Semi-empirical (xtb){880}")
        else:
            pass

    if args.run_command:
        # Remove results of last calculation
        if calc_dir.exists():
            rmtree(calc_dir)
        Path.mkdir(calc_dir)

        # Read input from Avogadro
        avo_input = json.loads(sys.stdin.read())
        # Extract the coords and write to file for use as xtb input
        geom = avo_input["xyz"]
        xyz_path = calc_dir / "input.xyz"
        with open(xyz_path, "w", encoding="utf-8") as xyz_file:
            xyz_file.write(str(geom))

        # Run calculation using xyz file
        result_path, energy = optimize(
            xyz_path,
            avo_input["charge"],
            avo_input["spin"]
            )
        # Convert geometry
        cjson_path = convert.xyz_to_cjson(result_path)
        # Open the cjson
        with open(cjson_path, encoding="utf-8") as result_cjson:
            cjson_geom = json.load(result_cjson)
        # Check for convergence
        # TO DO
        # Will need to look for "FAILED TO CONVERGE"
        # Convert energy for Avogadro
        energies = convert.convert_energy(energy, "hartree")
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
        with open(calc_dir / "result.cjson", "w", encoding="utf-8") as save_file:
            json.dump(result["cjson"], save_file, indent=2)
        # Pass back to Avogadro
        print(json.dumps(result))
