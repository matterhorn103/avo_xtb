# SPDX-FileCopyrightText: 2024 Matthew J. Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

"""Dispatch incoming feature requests to the appropriate module."""

import json
import sys


def run(args):
    # Handle --print-options for commands with dynamic options (Python fallback)
    if args.print_options:
        match args.feature:
            case "config":
                from .config import get_config_options

                print(json.dumps(get_config_options()))
            case "conformers":
                from .conformers import get_options

                print(json.dumps(get_options()))
            case "solvate":
                from .solvate import get_options

                print(json.dumps(get_options()))
            case "install-xtb":
                from .install_xtb import get_options

                print(json.dumps(get_options()))
            case "install-crest":
                from .install_crest import get_options

                print(json.dumps(get_options()))
        return

    # Read molecule + options input from stdin
    avo_input = json.loads(sys.stdin.read())

    # Extract options from new API structure if present, else use top-level keys
    # (old API passed options at top level; new API nests them under "options")
    options = avo_input.get("options", avo_input)

    output = None

    match args.feature:
        case "about":
            from .about import about

            output = about(avo_input)
        case "config":
            from .config import update_config

            update_config(options)
        case "energy":
            from .energy import energy

            output = energy(avo_input)
        case "opt":
            from .opt import opt

            output = opt(avo_input)
        case "freq":
            from .freq import freq

            output = freq(avo_input)
        case "smartopt":
            from .smartopt import ohess

            output = ohess(avo_input)
        case "orbitals":
            from .orbitals import orbitals

            output = orbitals(avo_input)
        case "conformers":
            from .conformers import conformers

            output = conformers(avo_input)
        case "tautomerize":
            from .tautomerize import tautomerize

            output = tautomerize(avo_input)
        case "protonate":
            from .protonate import protonate

            output = protonate(avo_input)
        case "deprotonate":
            from .deprotonate import deprotonate

            output = deprotonate(avo_input)
        case "solvate":
            from .solvate import solvate

            output = solvate(avo_input)
        case "install-xtb":
            from .install_xtb import install_xtb

            output = install_xtb(avo_input)
        case "install-crest":
            from .install_crest import install_crest

            output = install_crest(avo_input)
        case "open":
            from .open import open_calcs_dir

            open_calcs_dir()
        case "docs-xtb":
            from .docs_xtb import open_docs

            output = open_docs(avo_input)
        case "docs-crest":
            from .docs_crest import open_docs

            output = open_docs(avo_input)

    if output is not None:
        print(json.dumps(output))
