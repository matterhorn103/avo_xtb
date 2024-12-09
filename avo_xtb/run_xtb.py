# SPDX-FileCopyrightText: 2024 Matthew J. Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

"""User-facing command to run any arbitrary xtb command."""

import argparse
import json
import logging
import sys
from copy import deepcopy
from pathlib import Path
from shutil import copytree

from support import easyxtb


logger = logging.getLogger(__name__)


# Define behaviour of Run menu command
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--print-options", action="store_true")
    parser.add_argument("--run-command", action="store_true")
    parser.add_argument("--display-name", action="store_true")
    parser.add_argument("--lang", nargs="?", default="en")
    parser.add_argument("--menu-path", action="store_true")
    args = parser.parse_args()

    # Disable if xtb missing
    if easyxtb.XTB_BIN is None:
        quit()

    if args.print_options:
        options = {
            "inputMoleculeFormat": "xyz",
            "userOptions": {
                "save_dir": {
                    "type": "string",
                    "label": "Save results in",
                    "default": str(easyxtb.CALCS_DIR),
                    "order": 1.0,
                },
                # "Number of threads": {
                #    "type": "integer",
                #    #"label": "Number of cores",
                #    "minimum": 1,
                #    "default": 1,
                #    "order": 2.0,
                #    },
                # "Memory per core": {
                #    "type": "integer",
                #    #"label" "Memory per core",
                #    "minimum": 1,
                #    "default": 1,
                #    "suffix": " GB",
                #    "order": 3.0,
                #    },
                "help": {
                    "type": "text",
                    "label": "For help see",
                    "default": "https://xtb-docs.readthedocs.io/",
                    "order": 9.0,
                },
                "command": {
                    "type": "string",
                    "label": "Command to run",
                    "default": f"xtb <input_geometry> --opt {easyxtb.config['opt_lvl']} --chrg 0 --uhf 0",
                    "order": 10.0,
                },
                # "turbomole": {
                #     "type": "boolean",
                #     "label": "Use Turbomole geometry\n(use for periodic systems)",
                #     "default": False,
                #     "order": 4.0,
                # },
            },
        }
        # Add solvation to default command if found in user config
        if easyxtb.config["solvent"] is not None:
            options["userOptions"]["command"]["default"] += (
                f" --alpb {easyxtb.config['solvent']}"
            )
        # Add method to default command but only if not the default (currently GFN2-xTB)
        if easyxtb.config["method"] != 2:
            options["userOptions"]["command"]["default"] += f" --gfn {easyxtb.config['method']}"
        print(json.dumps(options))
    if args.display_name:
        print("Run…")
    if args.menu_path:
        print("Extensions|Semi-empirical (xtb){350}")

    if args.run_command:
        # Read input from Avogadro
        avo_input = json.loads(sys.stdin.read())
        # Extract the coords
        geom = easyxtb.Geometry.from_cjson(avo_input["cjson"])

        command = avo_input["command"].split()
        # Remove xtb and <input_geometry> placeholders
        command = []
        if command[0] == "xtb":
            # Got to be careful that we don't remove some other reference to xtb
            command = command[1:]
        try:
            command.remove("<input_geometry>")
        except ValueError:
            pass

        # Construct Calculation object
        # Run calculation; returns subprocess.CompletedProcess object and path to output.out
        calc = easyxtb.Calculation(
            input_geom=geom,
            program="xtb",
            command=command,
        )
        calc.run()

        # Format everything appropriately for Avogadro
        # Start by passing back an empty cjson, then add changes
        output = {
            "moleculeFormat": "cjson",
            "cjson": deepcopy(easyxtb.convert.empty_cjson),
        }

        # TODO Catch errors in xtb execution

        # Many different parts of the following may wish to report messages
        # Instantiate a message list and combine later
        message = []

        if hasattr(calc, "energy"):
            energies = easyxtb.convert.convert_energy(calc.energy, "hartree")
            output["cjson"]["properties"]["totalEnergy"] = round(energies["eV"], 7)
        if hasattr(calc, "output_geometry"):
            geom_cjson = calc.output_geometry.to_cjson()
            output["cjson"]["atoms"]["coords"] = geom_cjson["atoms"]["coords"]
        if hasattr(calc, "frequencies"):
            freq_cjson = easyxtb.convert.freq_to_cjson(calc.frequencies)
            output["cjson"]["vibrations"] = freq_cjson["vibrations"]
            # Inform user if there are negative frequencies
            if calc.frequencies[0]["frequency"] < 0:
                message.append(
                    "At least one negative frequency found!\n"
                    + "This is not a minimum on the potential energy surface.\n"
                    + "You should reoptimize the geometry.\n"
                    + "This can be avoided in future by using the Opt + Freq method."
                )
        if hasattr(calc, "output_molden"):
            # Check if orbitals were requested
            # Not sure how to keep orbital info at same time as any other calculation type
            # Currently avo only accepts one file format being passed back
            output["readProperties"] = True
            output["moleculeFormat"] = "molden"
            output["molden"] = calc.output_molden

        # Add all the info messages, separated by blank lines
        output["message"] = "\n\n".join(message)

        # Save result
        with open(easyxtb.CALCS_DIR / "result.cjson", "w", encoding="utf-8") as save_file:
            json.dump(output["cjson"], save_file, indent=2)

        # If user specified a save location, copy calculation directory to there
        if not (
            avo_input["save_dir"] in ["", None]
            or Path(avo_input["save_dir"]) == easyxtb.CALCS_DIR
        ):
            copytree(easyxtb.CALCS_DIR, Path(avo_input["save_dir"]), dirs_exist_ok=True)

        # Pass back to Avogadro
        print(json.dumps(output))
        logger.debug(f"The following dictionary was passed back to Avogadro: {output}")
