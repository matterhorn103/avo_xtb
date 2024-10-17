def parse_energy(output_string: str) -> float:
    """Find the final energy in an xtb output file and return as a float.
    
    Units vary depending on calculation type."""
    # but don't convert here as not all calculation types give in same units
    lines = output_string.split("\n")
    matched_lines = [line for line in lines if "TOTAL ENERGY" in line]
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
