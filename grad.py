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

from config import config, calc_dir
from run import run_xtb



def grad(geom_file, charge=0, multiplicity=1, solvation=True, grad_floats=True):
    spin = multiplicity - 1
    command = ["xtb", geom_file, "--grad", "--chrg", str(charge), "--uhf", str(spin)]
    # Add solvation if set globally
    if solvation and config["solvent"] is not None:
        command.append("--alpb")
        command.append(config["solvent"])
    # Run xtb from command line
    calc, out_file, energy = run_xtb(command, geom_file)
    # Get gradient from created file
    gradient = parse_gradient_file(out_file.with_name("gradient"), floats=grad_floats)

    # Geometry will be unchanged so just return values of interest
    return energy, gradient


# Parse Turbomole-format gradient files
def parse_gradient_file(gradient_file, floats=True):
    with open(gradient_file, encoding="utf-8") as file:
        lines = file.readlines()
        # First line reads $grad
        # Second line contains cycle no, energy, overall gradient
        # Last line reads $end
        coords_plus_grad = lines[2:-1]
        # First 50% of lines are just the coordinates
        grad_lines = coords_plus_grad[(len(coords_plus_grad) // 2):]
        # Note that we get lucky here and split() removes the trailing \n on each line
        grad_strings = [line.split() for line in grad_lines]
    # Return gradient as list of lists i.e. [[x,y,z],[x,y,z],...]
    # Coordinates are floats by default, strings on request
    if floats:
        grad_floats = [[float(x) for x in atom] for atom in grad_strings]
        return grad_floats
    else:
        return grad_strings
