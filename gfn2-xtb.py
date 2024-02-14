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

# First need to make sure we can use bits from the rest of avo_xtb
energy_dir = Path(__file__).parent
avo_xtb_dir = energy_dir.parent / "commands" / "avo_xtb"
# Add to to Python path
sys.path.append(str(avo_xtb_dir))

# Now can import what we need as if this script was in the avo_xtb folder
from config import calc_dir
from grad import grad
from convert import get_element_symbol


# Unlike other scripts in this package, this script provides energies and
# gradients calculated by xtb for use by Avogadro's calculation framework


# Simple function that formats a list of lists into an xyz file and saves it
# Expects coords to be strings!
def save_xyz(n_atoms, coords, filepath):
    lines = []
    lines.append(str(n_atoms))
    lines.append("")
    # Turn each atom list into a string, add all strings to list of lines
    lines.extend(["    ".join([x for x in atom]) for atom in coords])
    with open(filepath, "w", encoding="utf-8") as output_file:
        output_file.writelines("\n".join(lines))
        

# Define calculation loop
def run(original_input):
    input_file = calc_dir / "input.xyz"
    # First get charge, spin, coords from input cjson
    with open(Path(original_input), encoding="utf-8") as input_cjson:
        cjson = json.load(input_cjson)
        charge = cjson["properties"]["totalCharge"]
        multiplicity = cjson["properties"]["totalSpinMultiplicity"]
        all_coords = cjson["atoms"]["coords"]["3d"]
        all_element_numbers = cjson["atoms"]["elements"]["number"]
        # Format into list of lists in style of xyz file i.e. [[El,x,y,z],[El,x,y,z],...]
        coords = []
        for index, element in enumerate(all_element_numbers):
            atom = [get_element_symbol(element), str(all_coords[index * 3]), str(all_coords[(index * 3) + 1]), str(all_coords[(index * 3) + 2])]
            coords.append(atom)
        n_atoms = len(coords)
    # Check we can save this file
    save_xyz(n_atoms, coords, input_file)
    # Loop forever until killed by Avogadro
    while True:
        # Read new coordinates from stdin
        for atom_index in range(n_atoms):
            # Coordinates seem to be supplied as strings of "x.xxx y.yyy z.zzz" on a per-atom basis
            new_coordinates = input().split()
            for index, coord in enumerate(new_coordinates):
                coords[atom_index][index + 1] = coord
        # Save refreshed coordinates to file
        save_xyz(n_atoms, coords, input_file)
        
        # Run gradient calculation without solvation
        # Request gradient as strings to save converting
        energy_hartree, gradient = grad(input_file, charge, multiplicity, solvation=False, grad_floats=False)
        
        # Avo needs energy returned in kJ/mol
        energy_kJ = energy_hartree * 2625.4996395
        print("AvogadroEnergy:", str(energy_kJ))
        with open(calc_dir / "grad.txt", "w") as test:
            test.write(str(energy_kJ))

        # Now return gradient on each atom on line-by-line basis
        # Single spaces as separators between x y z
        #with open(calc_dir / "grad.txt", "w") as test:
            #test.write(str(gradient))
        print("AvogadroGradient:")
        for atom in gradient:
            print(atom[0], atom[1], atom[2])


metadata = {
    "inputFormat": "cjson",
    "identifier": "avo_xtb_gfn2-xtb",
    "name": "User-Friendly Name",
    "description": "Description of method or citation.",
    "elements": "1-86",
    "unitCell": False,
    "gradients": True,
    "ion": True,
    "radical": True,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata", action="store_true")
    parser.add_argument("--display-name", action="store_true")
    parser.add_argument("--lang", nargs="?", default="en")
    parser.add_argument("-f", "--file", default=None)
    args = parser.parse_args()

    if args.metadata:
        print(json.dumps(metadata))
    if args.display_name:
        print(metadata["name"])
    
    if args.file:
        # Remove results of last calculation
        if calc_dir.exists():
            rmtree(calc_dir)
        calc_dir.mkdir()
        run(args.file)