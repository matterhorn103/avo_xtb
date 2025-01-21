# SPDX-FileCopyrightText: 2024 Matthew J. Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

"""Provides a `Program` dataclass to hold details on command line executables."""

import logging
import os
import platform
from dataclasses import dataclass
from pathlib import Path
from shutil import which

from .configuration import BIN_DIR, config


logger = logging.getLogger(__name__)


@dataclass
class Program:
    """Represents a quantum chemical program that can be run from the command line."""
    name: str
    path: Path
    runtypes: list[str]


def find_bin(program: str) -> Path | None:
    """Return path to xtb or CREST binary as Path object, or None."""
    bin_name = f"{program}.exe" if platform.system() == "Windows" else program
    bin_path = None
    for possible_location in [
        BIN_DIR / bin_name,  # Normal binary or symlink to it
        BIN_DIR / program / bin_name,  # Old layout for xtb, current for CREST
        BIN_DIR
        / f"{program}-dist/bin/{bin_name}",  # Whole xtb distribution folder with nested binary directory
    ]:
        if possible_location.exists() and not possible_location.is_dir():
            bin_path = possible_location
            break
    # Otherwise check the PATH
    if not bin_path and which(bin_name) is not None:
        bin_path = Path(which(bin_name))
    logger.debug(f"{bin_name} binary location determined to be: {bin_path}")
    return bin_path


def resolve_bin(program: str) -> Path | None:
    """Get a resolved, absolute path to the requested program, or None if not found."""
    if f"{program}_bin" in config:
        path = Path(config[f"{program}_bin"])
        if not path.exists():
            path = find_bin(program)
    else:
        path = find_bin(program)
    if path is not None:
        # Resolve to make path absolute and simultaneously follow any symlinks
        path = path.resolve()
    return path


# Initialize and find the various binaries
# Confirm that those loaded from the config can be found
# A Program object is created for each binary as a global variable
# The path field for each will be set to None if the binary is not found anywhere
# Note that the binary paths are not actually saved to the config unless the user
# actively does so
XTB = Program(
    "xtb",
    resolve_bin("xtb"),
    [
        "scc",
        "grad",
        "vip",
        "vea",
        "vipea",
        "vomega",
        "vfukui",
        "dipro",
        "esp",
        "stm",
        "opt",
        "metaopt",
        "path",
        "modef",
        "hess",
        "ohess",
        "metadyn",
        "siman",
    ],
)

CREST = Program(
    "crest",
    resolve_bin("crest"),
    [
        "sp",
        "opt",
        "ancopt",
        "v1",
        "v2",
        "v2i",
        "v3",
        "v4",
        "entropy",
        "protonate",
        "deprotonate",
        "tautomerize",
        "cregen",
        "qcg",
        "msreact",
    ],
)

# Have to set environment variable XTBPATH so that parameterizations (e.g. of
# GFN0-xTB) are found
if XTB.path:
    os.environ["XTBPATH"] = str(XTB.path.parent.parent / "share/xtb")

logger.debug(f"{XTB.path=}")
logger.debug(f"{CREST.path=}")
