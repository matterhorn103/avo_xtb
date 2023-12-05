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

from config import config, calc_dir
import convert
from run import run_xtb


def frequencies(geom_file, charge=0, multiplicity=1):
    spin = multiplicity - 1
    command = ["xtb", geom_file, "--hess", "--chrg", str(charge), "--uhf", str(spin)]
    # Add solvation if set globally
    if config["solvent"] is not None:
        command.append("--alpb")
        command.append(config["solvent"])
    # Run xtb from command line
    calc, out_file, energy = run_xtb(command, geom_file)

    # Return the path of the Gaussian file generated
    return (geom_file.with_name("g98.out"))


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
            rmtree(calc_dir)
        Path.mkdir(calc_dir)

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
            avo_input["charge"],
            avo_input["spin"]
            )
        # Currently Avogadro fails to convert the g98 file to cjson itself
        # So we have to convert output in g98 format to cjson ourselves
        cjson_path = convert.g98_to_cjson(result_path)
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
            result["message"] = ("At least one negative frequency found!\n"
                                 "This is not a minimum on the potential energy surface.\n"
                                 "You should reoptimize the geometry.\n"
                                 "This can be avoided in future by using the Opt + Freq method.")

        # Save result
        with open(calc_dir / "result.cjson", "w", encoding="utf-8") as save_file:
            json.dump(result["cjson"], save_file)
        # Pass back to Avogadro
        print(json.dumps(result))
