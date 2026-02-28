# SPDX-FileCopyrightText: 2024 Matthew J. Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

"""Package initialization and entry point for the avo_xtb Avogadro plugin."""

import sys

import easyxtb

# Make sure stdout stream is always Unicode, as Avogadro expects
sys.stdout.reconfigure(encoding="utf-8")

# Piggyback the easyxtb config and add some extra plugin-specific things
plugin_defaults = {
    "energy_units": "kJ/mol",
    "xtb_opts": {},
    "crest_opts": {},
}
for k, v in plugin_defaults.items():
    if k not in easyxtb.config:
        easyxtb.config[k] = v


def main():
    """Entry point for the avo_xtb plugin.

    Avogadro calls the plugin as:
        avogadro-avo-xtb <identifier> [--lang <locale>] [--debug]
    with the molecule + options JSON on stdin.

    For backwards compatibility, --print-options is also supported for commands
    with dynamic options (config, conformers, solvate, install-xtb, install-crest).
    """
    import argparse

    from .run import run

    parser = argparse.ArgumentParser()
    parser.add_argument("feature")
    parser.add_argument("--lang", nargs="?", default="en")
    parser.add_argument("--debug", action="store_true")
    # Legacy/fallback support for dynamic options generation
    parser.add_argument("--print-options", action="store_true")
    args = parser.parse_args()

    if args.debug:
        import logging

        logging.basicConfig(level=logging.DEBUG)

    run(args)
