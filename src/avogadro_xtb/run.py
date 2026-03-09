# SPDX-FileCopyrightText: 2026 Matthew Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

import json
import logging

import easyxtb


logger = logging.getLogger(__name__)

# Piggyback the easyxtb config and add some extra plugin-specific things
plugin_defaults = {
    "energy_units": "kJ/mol",
    "xtb_opts": {},
    "crest_opts": {},
}
for k, v in plugin_defaults.items():
    if k not in easyxtb.config:
        easyxtb.config[k] = v


def sp(avo_input: dict) -> dict:
    cjson = avo_input["cjson"]
    geom = easyxtb.Geometry.from_cjson(cjson)

    # Run calculation; returns energy as float in hartree
    logger.debug("The plugin is requesting a single point energy calculation")
    calc = easyxtb.Calculation.sp(
        geom,
        options=easyxtb.config["xtb_opts"],
    )
    calc.run()

    # If an energy couldn't be parsed, will return None, so have to allow for that
    # Seems like a reasonable placeholder that should be obviously incorrect to anyone
    energy_hartree = 0.0 if calc.energy is None else calc.energy

    # Convert energy to eV for Avogadro, other units for users
    energies = easyxtb.convert.convert_energy(energy_hartree, "hartree")

    # Add changes to cjson
    cjson["properties"]["totalEnergy"] = round(energies["eV"], 7)
    # Partial charges if present
    if hasattr(calc, "partial_charges"):
        cjson["atoms"]["partialCharges"] = calc.partial_charges

    # Format output appropriately for Avogadro
    output = {"cjson": cjson}
    # Currently Avogadro ignores the energy result so tell the user via a message
    output["message"] = (
        f"Energy from GFN{easyxtb.config['method']}-xTB:\n"
        + f"{str(round(energy_hartree, 7))} hartree\n"
        + f"{str(round(energies['eV'], 7))} eV\n"
        + f"{str(round(energies['kJ'], 7))} kJ/mol\n"
        + f"{str(round(energies['kcal'], 7))} kcal/mol\n"
    )

    return output


def cleanup_after_opt(cjson: dict) -> dict:
    """Returns a cjson dict minus any data that is no longer meaningful after
    a geometry change."""

    cleaned = cjson

    # Frequencies and orbitals
    for field in ["vibrations", "basisSet", "orbitals", "cube"]:
        if field in cleaned:
            del cleaned[field]
    # Atomic charges
    if "formalCharges" in cleaned["atoms"]:
        del cleaned["atoms"]["formalCharges"]
    if "partialCharges" in cleaned["atoms"]:
        del cleaned["atoms"]["partialCharges"]

    return cleaned


def opt(avo_input: dict, ohess: bool) -> dict:
    cjson = avo_input["cjson"]
    geom = easyxtb.Geometry.from_cjson(cjson)

    # Run calculation
    logger.debug("The plugin is requesting a geometry optimization")
    if ohess:
        calc = easyxtb.Calculation.opt(
            geom,
            options=easyxtb.config["xtb_opts"],
        )
    else:
        calc = easyxtb.Calculation.ohess(
            geom,
            options=easyxtb.config["xtb_opts"],
        )
    calc.run()

    # Convert geometry to cjson
    geom_cjson = calc.output_geometry.to_cjson()

    # Check for convergence
    # TODO
    # Will need to look for "FAILED TO CONVERGE"

    # Get energy for Avogadro
    energies = easyxtb.convert.convert_energy(calc.energy, "hartree")

    # Update CJSON
    # Remove anything that is now unphysical after the optimization
    cjson = cleanup_after_opt(cjson)

    # Add data from calculation
    cjson["atoms"]["coords"] = geom_cjson["atoms"]["coords"]
    cjson["properties"]["totalEnergy"] = round(energies["eV"], 7)
    # Partial charges if present
    if hasattr(calc, "partial_charges"):
        cjson["atoms"]["partialCharges"] = calc.partial_charges

    # Format output appropriately for Avogadro
    output = {"moleculeFormat": "cjson", "cjson": cjson}

    return output


def freq(avo_input: dict) -> dict:
    cjson = avo_input["cjson"]
    geom = easyxtb.Geometry.from_cjson(cjson)

    # Run calculation; returns set of frequency data
    logger.debug("The plugin is requesting a frequency calculation")
    freqs = easyxtb.calculate.frequencies(
        geom,
        options=easyxtb.config["xtb_opts"],
    )

    # Format the frequencies in the appropriate way for CJSON
    freq_cjson = easyxtb.convert.freq_to_cjson(freqs)

    # Add frequency data to the CJSON
    cjson["vibrations"] = freq_cjson["vibrations"]

    # Format output appropriately for Avogadro
    output = {"moleculeFormat": "cjson", "cjson": cjson}

    # Inform user if there are negative frequencies
    if freqs[0]["frequency"] < 0:
        output["message"] = (
            "At least one negative frequency found!\n"
            + "This is not a minimum on the potential energy surface.\n"
            + "You should reoptimize the geometry.\n"
            + "This can be avoided in future by using the Smart Opt method."
        )

    return output


def orbitals(avo_input: dict) -> dict:
    cjson = avo_input["cjson"]
    geom = easyxtb.Geometry.from_cjson(cjson)

    # Run calculation; returns Molden output file as string
    logger.debug("The plugin is requesting a molecular orbitals calculation")
    molden_string = easyxtb.calculate.orbitals(
        geom,
        options=easyxtb.config["xtb_opts"],
    )

    # Format everything appropriately for Avogadro
    # Just pass orbitals file with instruction to read only properties
    output = {
        "readProperties": True,
        "moleculeFormat": "molden",
        "molden": molden_string,
        "cjson": cjson,
    }
    # As it stands, this means any other properties will be wiped
    # If there were e.g. frequencies in the original cjson, notify the user
    if "vibrations" in cjson:
        output["message"] = (
            "Calculation complete!\n"
            "The vibrational frequencies may have been lost in this process.\n"
            "Please recalculate them if they are missing and still desired.\n"
        )
    else:
        output["message"] = "Calculation complete!"

    # Save orbitals file as well
    with open(easyxtb.TEMP_DIR / "result.molden", "w", encoding="utf-8") as f:
        f.write(molden_string)

    return output


def run(
    avo_input: dict,
    feature: str,
    **args,  # Ignore anything else
) -> dict:
    match feature:
        case "sp":
            output = sp(avo_input)
        case "opt":
            output = opt(avo_input, ohess=False)
        case "smartopt":
            output = opt(avo_input, ohess=True)
        case "freq":
            output = freq(avo_input)
        case "orbitals":
            output = orbitals(avo_input)
        case _:
            output = {"error": "The runtype was not recognized!"}

    # Save result
    with open(easyxtb.TEMP_DIR / "result.cjson", "w", encoding="utf-8") as f:
        json.dump(output["cjson"], f, indent=2)
    return output
