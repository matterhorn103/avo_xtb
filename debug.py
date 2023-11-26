import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from convert import obabel_path

def debug():
    # Whatever we want to test
    # Return a string that can then be displayed in Avogadro

    feedback = str(obabel_path)

    return feedback

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
        options = {"inputMoleculeFormat": "cjson"}
        print(json.dumps(options))
    if args.display_name:
        print("Debug")
    if args.menu_path:
        print("Extensions|Semi-empirical (xtb)")

    if args.run_command:
        # Read input from Avogadro
        avo_input = json.loads(sys.stdin.read())
        # Execute whatever the debug code is
        feedback = debug()
        # Format appropriately for Avogadro
        # Start by passing back the original cjson, then add changes
        result = {"molecularFormat": "cjson", "cjson": avo_input["cjson"], "message": feedback}
        # Pass back to Avogadro
        print(json.dumps(result))
