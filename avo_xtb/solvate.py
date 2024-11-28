# SPDX-FileCopyrightText: 2024 Matthew J. Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

import argparse
import json
import logging
import sys
from copy import deepcopy
from pathlib import Path

from support import easyxtb


logger = logging.getLogger(__name__)


def split_cjson_by_layer(cjson: dict) -> list[dict]:
    """Separate a CJSON into multiple CJSONs according to which layer atoms are in.
    
    For now drops all data except atom and bond information.
    
    All layers are assumed to contain neutral singlets, except layer 0, which is given
    the total charge and multiplicity of the original CJSON.
    """
    output = []
    for layer_index in range(max(cjson["atoms"]["layer"]) + 1):
        layer = deepcopy(easyxtb.convert.empty_cjson)
        atoms_in_layer = []
        for atom_index, atom_layer in enumerate(cjson["atoms"]["layer"]):
            if atom_layer == layer_index:
                atoms_in_layer.append(atom_index)
        for atom_index in atoms_in_layer:
            layer["atoms"]["coords"]["3d"].extend(
                cjson["atoms"]["coords"]["3d"][3*atom_index:3*(atom_index+1)]
            )
            layer["atoms"]["elements"]["number"].append(
                cjson["atoms"]["elements"]["number"][atom_index]
            )
        for bond_index, bond_order in enumerate(cjson["bonds"]["order"]):
            bond_members = (
                cjson["bonds"]["connections"]["index"][2*bond_index:2*(bond_index+1)]
            )
            if all([atom in atoms_in_layer for atom in bond_members]):
                layer["bonds"]["connections"]["index"].extend(bond_members)
                layer["bonds"]["order"].append(bond_order)
        if layer_index == 0:
            layer["properties"]["totalCharge"] = cjson["properties"]["totalCharge"]
            layer["properties"]["totalSpinMultiplicity"] = cjson["properties"]["totalSpinMultiplicity"]
        output.append(layer)
    return output


def solvate(avo_input: dict) -> dict:
    # Extract the cjson
    full_cjson = avo_input["cjson"]
    # Sort atoms based on layer
    layers = split_cjson_by_layer(full_cjson)

    # Adjust for difference in indexing between what the user's choice was based on 
    # (Avogadro GUI uses 1-indexing) and what we receive (CJSON uses 0-indexing)
    solute_layer = avo_input["solute_layer"] - 1
    solvent_layer = avo_input["solvent_layer"] - 1

    solute_cjson = layers[solute_layer]
    solvent_cjson = layers[solvent_layer]
    solute_geom = easyxtb.Geometry.from_cjson(solute_cjson)
    solvent_geom = easyxtb.Geometry.from_cjson(solvent_cjson)

    # Run calculation; returns new Geometry
    output_geom = easyxtb.calculate.solvate(
        solute_geom,
        solvent_geom,
        nsolv=avo_input["nsolv"],
        method=2,
    )

    # Format everything appropriately for Avogadro
    output = {
        "moleculeFormat": "cjson",
        "cjson": output_geom.to_cjson(),
    }

    # Save result
    with open(easyxtb.TEMP_DIR / "result.cjson", "w", encoding="utf-8") as save_file:
        json.dump(output["cjson"], save_file, indent=2)
    
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--print-options", action="store_true")
    parser.add_argument("--run-command", action="store_true")
    parser.add_argument("--display-name", action="store_true")
    parser.add_argument("--lang", nargs="?", default="en")
    parser.add_argument("--menu-path", action="store_true")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    # Disable if xtb or crest missing
    if easyxtb.XTB_BIN is None or easyxtb.CREST_BIN is None:
        quit()

    if args.print_options:
        options = {
            "userOptions": {
                "solute_layer": {
                    "type": "integer",
                    "label": "Layer containing the solute",
                    "default": 1,
                    "minimum": 1,
                    "maximum": 100,
                    "order": 1.0,
                },
                "solvent_layer": {
                    "type": "integer",
                    "label": "Layer containing a solvent molecule",
                    "default": 2,
                    "minimum": 1,
                    "maximum": 100,
                    "order": 2.0,
                },
                "nsolv": {
                    "type": "integer",
                    "label": "Number of solvent molecules to add",
                    "default": 4,
                    "minimum": 1,
                    "maximum": 1000,
                    "order": 3.0,
                },
            },
        }
        print(json.dumps(options))

    if args.display_name:
        print("Solvate…")

    if args.menu_path:
        print("Extensions|Semi-empirical (xtb){760}")

    if args.run_command:
        # Read input from Avogadro
        avo_input = json.loads(sys.stdin.read())
        output = solvate(avo_input)
        # Pass back to Avogadro
        print(json.dumps(output))
        logger.debug(f"The following dictionary was passed back to Avogadro: {output}")
    
    if args.test:
        with open(
            Path(__file__).parent / "tests/files/solvate.cjson", encoding="utf-8"
        ) as f:
            avo_input = json.load(f)
        cjson = avo_input["cjson"]
        layers = split_cjson_by_layer(cjson)
        print(layers[0])
        print(layers[1])
