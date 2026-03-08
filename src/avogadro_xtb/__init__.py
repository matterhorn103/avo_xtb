# SPDX-FileCopyrightText: 2026 Matthew Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

"""Package initialization and entry point for the avogadro-xtb Avogadro plugin."""

import argparse
import json
import logging
import sys

from .run import run

# Make sure stdout stream is always Unicode, as Avogadro expects
sys.stdout.reconfigure(encoding="utf-8")

logger = logging.getLogger(__name__)


def main():
    """Entry point for the plugin."""

    parser = argparse.ArgumentParser()
    # It is planned to offer multiple feature types in future
    # When the args for each feature differ, we have to delegate to subparsers
    subparsers = parser.add_subparsers(dest="feature")

    # Each feature gets its own subparser, where the `title` of each
    # subparser must match the `identifier` for the feature
    # We then add the arguments specific to each feature to its subparser

    # We can also define common shared arguments and have all feature parsers
    # inherit them without having to define them for every feature separately
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--lang", nargs="?", default="en")
    common.add_argument("--debug", action="store_true")

    subparsers.add_parser("sp", parents=[common])
    subparsers.add_parser("opt", parents=[common])
    subparsers.add_parser("smartopt", parents=[common])
    subparsers.add_parser("freq", parents=[common])

    args = parser.parse_args()

    # Read (initial) input from Avogadro
    avo_input = json.loads(sys.stdin.read())

    output = run(avo_input, **args)

    print(json.dumps(output))
    logger.debug(f"The following dictionary was passed back to Avogadro: {output}")
