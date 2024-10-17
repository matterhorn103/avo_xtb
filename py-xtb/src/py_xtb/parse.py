# Copyright (c) 2023-2024, Matthew J. Milner
# This file is part of py-xtb which is released under the BSD 3-Clause License.
# See LICENSE or go to https://opensource.org/license/BSD-3-clause for full details.

def parse_energy(output_string: str) -> float:
    """Find the final energy in an xtb output file and return as a float.
    
    Units vary depending on calculation type."""
    # but don't convert here as not all calculation types give in same units
    lines = output_string.split("\n")
    matched_lines = [l for l in lines if "TOTAL ENERGY" in l]
    if len(matched_lines) > 0:
        energy_line = matched_lines[-1]
    else:
        return None
    for section in energy_line.split():
        try:
            energy = float(section)
        except ValueError:
            continue
    return energy


def parse_frequencies(output_string: str) -> list[dict]:
    """Read the vibrational frequency information from a Gaussian 98 format output file.

    The results are returned as a list of the frequencies, with each entry a dict of
    information for the frequency.
    The eigenvectors for a frequency are returned as a list of lists of the form [x,y,z]
    for each atom.
    """
    frequencies = []
    freq_table = output_string.split(
        "reduced masses (AMU), force constants (mDyne/A) and normal coordinates:\n"
    )[1].split("\n")
    # Work out how many frequencies we have, how many blocks of 3 there are, and how
    # many lines each block has
    n_blocks = 0
    for l in freq_table:
        if l.startswith(" Frequencies --"):
            n_blocks += 1
    len_block = len(freq_table) // n_blocks
    n_freqs = freq_table[(n_blocks - 1) * len_block].split()[-1]
    for b in range(n_blocks):
        block = freq_table[b * len_block:(b * len_block) + len_block]
        modes = block[0].split()
        symmetries = block[1].split()
        # Prune the row headings as we go
        # Descriptions here are those found in the files themselves
        # Harmonic frequencies (cm**-1)
        freqs = block[2].split("--")[1].split()
        # reduced masses (AMU)
        red_masses = block[3].split("--")[1].split()
        # force constants (mDyne/A) - seem to be written as all zeroes
        frc_consts = block[4].split("--")[1].split()
        # IR intensities (km*mol⁻¹)
        ir_intensities = block[5].split("--")[1].split()
        # Raman scattering activities (A**4/amu) - not calculated by xtb, written as all zeroes
        raman_activities = block[6].split("--")[1].split()
        # Raman depolarization ratios - also seem to be written as all zeroes
        depolar = block[7].split("--")[1].split()
        # normal coordinates - of the vibrations
        coords = [l.split()[2:] for l in block[9:]]
        # i is 0 to 2, n is the number of the frequency in the whole set
        for i, n in enumerate(modes):
            n = int(n)
            freq_info = {
                "mode": n,
                "frequency": float(freqs[i]),
                "reduced_mass": float(red_masses[i]),
                "force_constant": float(frc_consts[i]),
                "ir_intensity": float(ir_intensities[i]),
                "raman_scattering_activity": float(raman_activities[i]),
                "raman_depolarization_ratio": float(depolar[i]),
                "eigenvectors": [
                    [float(atom[i]), float(atom[i+1]), float(atom[i+2])]
                    for atom in coords
                ],
            }
            frequencies.insert(n, freq_info)
    return frequencies


if __name__ == "__main__":
    with open("/home/matt/.local/share/py-xtb/last/g98.out") as f:
        output_string = f.read()
    for x in parse_frequencies(output_string):
        print(x)
