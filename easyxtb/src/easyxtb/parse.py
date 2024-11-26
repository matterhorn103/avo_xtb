# SPDX-FileCopyrightText: 2024 Matthew J. Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

"""Functions to parse specific data from output files."""


def parse_charge_spin(output_string: str) -> tuple[int, int]:
    """Get the charge and spin that xtb used for a calculation."""
    lines = output_string.split("\n")
    charge_lines = [l for l in lines if ":  net charge" in l]
    spin_lines = [l for l in lines if ":  unpaired electrons" in l]
    charge = int(charge_lines[0].split()[3])
    spin = int(spin_lines[0].split()[3])
    return (charge, spin)


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
    """Read the vibrational frequency information from an xtb output file.

    The results are returned as a list of the frequencies, with each entry a dict of
    information for the frequency.
    The eigenvectors for the frequencies are not contained in the xtb output file – if
    they are required, use `parse_g98_frequencies()` on the `g98.out` file instead.
    """
    # TODO
    pass


def parse_g98_frequencies(gaussian_output_string: str) -> list[dict]:
    """Read the vibrational frequency information from a Gaussian 98 format output file.

    The results are returned as a list of the frequencies, with each entry a dict of
    information for the frequency.
    The eigenvectors for a frequency are returned as a list of lists of the form [x,y,z]
    for each atom.
    """
    frequencies = []
    freq_table = gaussian_output_string.split(
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
        # Raman scattering activities (A**4/amu) - seems to be written as all zeroes, even though
        # they are also printed to the xtb output file
        raman_activities = block[6].split("--")[1].split()
        # Raman depolarization ratios - also seem to be written as all zeroes
        depolar = block[7].split("--")[1].split()
        # normal coordinates - of the vibrations
        coords = [l.split()[2:] for l in block[9:]]
        # i is 0 to 2, n is the number of the frequency in the whole set
        for i, n in enumerate(modes):
            n = int(n)
            # Leave out (commented out) the things that xtb doesn't even print to standard output
            freq_info = {
                "mode": n,
                "symmetry": symmetries[i],
                "frequency": float(freqs[i]),
                "reduced_mass": float(red_masses[i]),
                #"force_constant": float(frc_consts[i]),
                "ir_intensity": float(ir_intensities[i]),
                "raman_scattering_activity": float(raman_activities[i]),
                #"raman_depolarization_ratio": float(depolar[i]),
                "eigenvectors": [
                    [float(atom[3*i]), float(atom[3*i+1]), float(atom[3*i+2])]
                    for atom in coords
                ],
            }
            frequencies.insert(n, freq_info)
    return frequencies


def parse_orbitals(output_string: str) -> list[dict]:
    """Read the molecular orbital energy and occupancies from an xtb output file.

    The results are returned as a list of the MOs, with each entry a dict of information
    for the MO.
    Details on the GTO basis set and the coefficients for each MO are not contained in
    the xtb output file, so for the data needed to visualize the molecular orbitals see 
    the `molden.input` file instead.
    """
    # TODO
    pass
