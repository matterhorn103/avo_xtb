# SPDX-FileCopyrightText: 2024 Matthew J. Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

"""
Provides both the key `Calculation` class and a function-based calculation API.

The `Calculation` object provides the infrastructure and methods to launch a calculation
on the command line and is used by all other calculation options.

The function-based API returns just the values of interest for a given geometry in a
quick and intuitive fashion, without the user having to worry about `Calculation`
objects.

Both are designed to be run on `Geometry` objects.
"""

import logging
import os
import subprocess
from pathlib import Path
from shutil import rmtree

from .configuration import config, XTB_BIN, CREST_BIN, TEMP_DIR
from .geometry import Geometry
from .parse import parse_energy, parse_g98_frequencies


logger = logging.getLogger(__name__)


available_runtypes = {
    "xtb": [
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
    "crest": [
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
}


class Calculation:

    def __init__(
        self,
        program: str | os.PathLike = "xtb",
        runtype: str | None = None,
        runtype_args: list[str] | None = None,
        options: dict | None = None,
        command: list[str] | None = None,
        input_geometry: Geometry | None = None,
        calc_dir: os.PathLike | None = None,
    ):
        """A convenience object to prepare, launch, and hold the results of
        calculations.
        
        `options` are the flags passed to `xtb` or `crest` and should be given
        without preceding minuses, as the appropriate number will be added
        automatically.
        To use a flag that takes no argument, set the value to `True`.
        Flags with values of `False` or `None` will not be passed.

        Note that any contents of `calc_dir` will be removed when the calculation
        begins.
        """
        if program == "xtb":
            self.program_path = XTB_BIN
            self.program = "xtb"
        elif program == "crest":
            self.program_path = CREST_BIN
            self.program = "crest"
        else:
            self.program_path = Path(program)
            if "xtb" in self.program_path.name:
                self.program = "xtb"
            elif "crest" in self.program_path.name:
                self.program = "crest"

        if runtype:
            self.runtype = runtype
        elif options:
            # Runtype not specified but options were passed, so default runtype (single
            # point) is being requested
            self.runtype = None
        elif command:
            # User has passed full command themselves
            first_flag = command.split()[0].lstrip("-")
            if first_flag in available_runtypes[self.program]:
                self.runtype = first_flag
        else:
            # Just a simple single point with no special options or flags or anything
            self.runtype = None
        self.runtype_args = runtype_args if runtype_args else []
        self.options = options if options else {}
        self.command = command
        self.input_geometry = input_geometry
        self.calc_dir = Path(calc_dir) if calc_dir else TEMP_DIR
        logger.info(f"New Calculation created for runtype {self.runtype} with {self.program}")
    
    def run(self):
        """Run calculation with xtb or crest, storing the output, the saved output file,
        and the parsed energy, as well as the `subprocess` object."""

        logger.debug(f"Calculation of runtype {self.runtype} has been asked to run")
        logger.debug(f"The calculation will be run in the following directory: {self.calc_dir}")

        # Make sure directory nominated for calculation exists and is empty
        if self.calc_dir.exists():
            for x in self.calc_dir.iterdir():
                if x.is_file():
                    x.unlink()
                elif x.is_dir():
                    rmtree(x)
        else:
            self.calc_dir.mkdir(parents=True)

        # Save geometry to file
        geom_file = self.calc_dir / "input.xyz"
        logger.debug(f"Saving input geometry to {geom_file}")
        self.input_geometry.write_xyz(geom_file)
        # We are using proper paths for pretty much everything so it shouldn't be
        # necessary to change the working dir
        # But we do anyway to be absolutely that xtb runs correctly and puts all the
        # output here
        os.chdir(self.calc_dir)
        logger.debug(f"Working directory changed to {Path.cwd()}")
        self.output_file = geom_file.with_name("output.out")
        
        if self.command:
            # If arguments were passed by the user, use them as is
            command = self.command
        else:
            # Build command line args
            # "xtb"
            command = [str(self.program_path)]
            # Charge and spin from the initial Geometry
            if "chrg" not in self.options and self.input_geometry.charge != 0:
                command.extend(["--chrg", str(self.input_geometry.charge)])
            if "uhf" not in self.options and self.input_geometry.spin != 0:
                command.extend(["--uhf", str(self.input_geometry.spin)])
            # Any other options
            for flag, value in self.options.items():
                # Add appropriate number of minuses to flags
                if len(flag) == 1:
                    flag = "-" + flag
                else:
                    flag = "--" + flag
                if value is True:
                    command.append(flag)
                elif value is False or value is None:
                    continue
                else:
                    command.extend([flag, str(value)])
            # Which calculation to run
            if self.runtype is None:
                # Simple single point
                pass
            else:
                command.extend([
                    "--" + self.runtype,
                    *self.runtype_args,
                    "--",
                ])
            # Path to the input geometry file, preceded by a -- to ensure that it is not
            # parsed as an argument to the runtype
            command.extend(["--", str(geom_file)])
        logger.debug(f"Calculation will be run with the command: {' '.join(command)}")
        
        # Run xtb or crest from command line
        logger.debug("Running calculation in new subprocess...")
        subproc = subprocess.run(command, capture_output=True, encoding="utf-8")
        logger.debug("...calculation complete.")

        # Store output
        self.output = subproc.stdout
        # Also save it to file
        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write(self.output)
            logger.debug(f"Calculation output saved to {self.output_file}")
        
        # Store the subprocess.CompletedProcess object too
        self.subproc = subproc

        # Do all post-calculation processing according to which program was run
        if self.program == "crest":
            self.process_crest()
        else:
            self.process_xtb()

    def process_xtb(self):

        # First do generic operations that apply to many calculation types
        # Extract energy from output (if not found, returns None)
        self.energy = parse_energy(self.output)
        logger.debug(f"Final energy parsed from output file: {self.energy}")
        # If there's an output geometry, read it
        if self.output_file.with_name("xtbopt.xyz").exists():
            logger.debug(f"Output geometry found at {self.output_file.with_name('xtbopt.xyz')}")
            self.output_geometry = Geometry.from_file(
                self.output_file.with_name("xtbopt.xyz"),
                charge=self.input_geometry.charge,
                spin=self.input_geometry.spin,
            )
            logger.debug("Read output geometry")
        else:
            # Assume geom was the same at end of calc as at beginning
            logger.debug("No output geometry found - final geometry assumed to be same as initial")
            self.output_geometry = self.input_geometry
        # Orbital info
        # If Molden output was requested, read the file
        if self.options.get("molden", False):
            logger.debug("Molden output was requested, so checking for file")
            with open(self.output_file.with_name("molden.input"), encoding="utf-8") as f:
                molden_string = f.read()
            self.output_molden = molden_string
            logger.debug("Molden output was found and read")
        
        # Now do more specific operations based on calculation type
        match self.runtype:
            case "hess" | "ohess":
                logger.debug("Frequencies were requested, so checking for file")
                # Read the Gaussian output file with frequencies
                with open(self.output_file.with_name("g98.out"), encoding="utf-8") as f:
                    g98_string = f.read()
                self.frequencies = parse_g98_frequencies(g98_string)
            case _:
                pass

    def process_crest(self):
        match self.runtype:
            case "v1" | "v2" | "v2i" | "v3" | "v4" | None:
                # Conformer search
                logger.debug("A conformer search was requested, so checking for files")
                # Get energy and geom of lowest conformer
                best = Geometry.from_file(
                    self.output_file.with_name("crest_best.xyz"),
                    charge=self.input_geometry.charge,
                    spin=self.input_geometry.spin,
                )
                logger.debug(f"Geometry of lowest energy conformer read from {self.output_file.with_name('crest_best.xyz')}")
                self.output_geometry = best
                self.energy = float(best._comment)
                logger.debug(f"Energy of lowest energy conformer: {self.energy}")
                # Get set of conformers
                conformer_geoms = Geometry.from_file(
                    self.output_file.with_name("crest_conformers.xyz"),
                    multi=True,
                    charge=self.input_geometry.charge,
                    spin=self.input_geometry.spin,
                )
                logger.debug(f"Geometries of conformers read from {self.output_file.with_name('crest_conformers.xyz')}")
                self.conformers = [
                    {"geometry": geom, "energy": float(geom._comment)}
                    for geom in conformer_geoms
                ]
                logger.debug(f"Found {len(self.conformers)} conformers in the ensemble")
                # By convention the first in the file is the lowest but make sure anyway
                self.conformers = sorted(self.conformers, key=lambda x: x["energy"])
            case "protonate":
                # Protonation site screening
                logger.debug("A protonation site screening was requested, so checking for files")
                # Get set of tautomers
                tautomer_geoms = Geometry.from_file(
                    self.output_file.with_name("protonated.xyz"),
                    multi=True,
                    charge=self.input_geometry.charge + 1,
                    spin=self.input_geometry.spin,
                )
                logger.debug(f"Geometries of tautomers read from {self.output_file.with_name('protonated.xyz')}")
                self.tautomers = [
                    {"geometry": geom, "energy": float(geom._comment)}
                    for geom in tautomer_geoms
                ]
                logger.debug(f"Found {len(self.tautomers)} tautomers in the ensemble")
                # By convention the first in the file is the lowest but make sure anyway
                self.tautomers = sorted(self.tautomers, key=lambda x: x["energy"])
                # Get energy and geom of lowest tautomer
                best = self.tautomers[0]
                self.output_geometry = best["geometry"]
                self.energy = best["energy"]
                logger.debug(f"Energy of lowest energy tautomer: {self.energy}")
            case "deprotonate":
                # Deprotonation site screening
                logger.debug("A deprotonation site screening was requested, so checking for files")
                # Get set of tautomers
                tautomer_geoms = Geometry.from_file(
                    self.output_file.with_name("deprotonated.xyz"),
                    multi=True,
                    charge=self.input_geometry.charge - 1,
                    spin=self.input_geometry.spin,
                )
                logger.debug(f"Geometries of tautomers read from {self.output_file.with_name('deprotonated.xyz')}")
                self.tautomers = [
                    {"geometry": geom, "energy": float(geom._comment)}
                    for geom in tautomer_geoms
                ]
                logger.debug(f"Found {len(self.tautomers)} tautomers in the ensemble")
                # By convention the first in the file is the lowest but make sure anyway
                self.tautomers = sorted(self.tautomers, key=lambda x: x["energy"])
                # Get energy and geom of lowest tautomer
                best = self.tautomers[0]
                self.output_geometry = best["geometry"]
                self.energy = best["energy"]
                logger.debug(f"Energy of lowest energy tautomer: {self.energy}")
            case _:
                pass


def energy(
    input_geometry: Geometry,
    solvation: str | None = None,
    method: int = 2,
    n_proc: int | None = None,
    return_calc: bool = False,
) -> float | tuple[float, Calculation]:
    """Calculate energy in hartree for given geometry."""

    calc = Calculation(
        input_geometry=input_geometry,
        options={
            "gfn": method,
            "alpb": solvation,
            "p": n_proc if n_proc else config["n_proc"],
        },
    )
    calc.run()
    if return_calc:
        return calc.energy, calc
    else:
        return calc.energy


def optimize(
    input_geometry: Geometry,
    solvation: str | None = None,
    method: int = 2,
    level: str = "normal",
    n_proc: int | None = None,
    return_calc: bool = False,
) -> Geometry | tuple[Geometry, Calculation]:
    """Optimize the geometry, starting from the provided initial geometry, and return
    the optimized geometry."""

    calc = Calculation(
        input_geometry=input_geometry,
        runtype="opt",
        runtype_args=[level],
        options={
            "gfn": method,
            "alpb": solvation,
            "p": n_proc if n_proc else config["n_proc"],
        },
    )
    calc.run()
    # Check for convergence
    # TODO
    # Will need to look for "FAILED TO CONVERGE"
    if return_calc:
        return calc.output_geometry, calc
    else:
        return calc.output_geometry


def frequencies(
    input_geometry: Geometry,
    solvation: str | None = None,
    method: int = 2,
    n_proc: int | None = None,
    return_calc: bool = False,
) -> list[dict] | tuple[list[dict], Calculation]:
    """Calculate vibrational frequencies and return results as a list of dicts."""

    calc = Calculation(
        input_geometry=input_geometry,
        runtype="hess",
        options={
            "gfn": method,
            "alpb": solvation,
            "p": n_proc if n_proc else config["n_proc"],
        },
    )
    calc.run()
    if return_calc:
        return calc.frequencies, calc
    else:
        return calc.frequencies


def opt_freq(
    input_geometry: Geometry,
    solvation: str | None = None,
    method: int = 2,
    level: str = "normal",
    n_proc: int | None = None,
    auto_restart: bool = True,
    return_calc: bool = False,
) -> tuple[Geometry, list[dict]] | tuple[Geometry, list[dict], Calculation]:
    """Optimize geometry then calculate vibrational frequencies.
    
    If a negative frequency is detected by xtb, it recommends to restart the calculation
    from a distorted geometry that it provides, so this is done automatically if
    applicable by default.
    """

    calc = Calculation(
        input_geometry=input_geometry,
        runtype="ohess",
        runtype_args=[level],
        options={
            "gfn": method,
            "alpb": solvation,
            "p": n_proc if n_proc else config["n_proc"],
        },
    )
    calc.run()

    # Check for distorted geometry
    # (Generated automatically by xtb if result had negative frequency)
    # If found, rerun
    distorted_geom_file = calc.output_file.with_name("xtbhess.xyz")
    while distorted_geom_file.exists() and auto_restart:
        calc = Calculation(
            input_geometry=Geometry.from_file(distorted_geom_file, charge=input_geometry.charge, spin=input_geometry.spin),
            runtype="ohess",
            runtype_args=[level],
            options={
                "gfn": method,
                "alpb": solvation,
                "p": n_proc if n_proc else config["n_proc"],
            },
        )
        calc.run()

    if return_calc:
        return calc.output_geometry, calc.frequencies, calc
    else:
        return calc.output_geometry, calc.frequencies


def orbitals(
    input_geometry: Geometry,
    solvation: str | None = None,
    method: int = 2,
    n_proc: int | None = None,
    return_calc: bool = False,
) -> str | tuple[str, Calculation]:
    """Calculate molecular orbitals for given geometry.
    
    Returns a string of the Molden-format output file, which contains principally the
    GTO and MO information.
    """

    calc = Calculation(
        input_geometry=input_geometry,
        options={
            "molden": True,
            "gfn": method,
            "alpb": solvation,
            "p": n_proc if n_proc else config["n_proc"],
        },
    )
    calc.run()
    if return_calc:
        return calc.output_molden, calc
    else:
        return calc.output_molden


def conformers(
    input_geometry: Geometry,
    solvation: str | None = None,
    method: int = 2,
    ewin: int | float = 6,
    hess: bool = False,
    n_proc: int | None = None,
    return_calc: bool = False,
) -> list[dict]:
    """Simulate a conformer ensemble and return set of conformer Geometries and energies.

    The returned conformers are ordered from lowest to highest energy.

    All conformers within <ewin> kcal/mol are kept.
    If hess=True, vibrational frequencies are calculated and the conformers reordered by Gibbs energy.
    """
    method_flag = f"gfn{method}"
    calc = Calculation(
        program="crest",
        input_geometry=input_geometry,
        runtype="v3",
        options={
            "xnam": XTB_BIN,
            method_flag: True,
            "alpb": solvation,
            "ewin": ewin,
            "T": n_proc if n_proc else config["n_proc"],
        },
    )
    if hess:
        calc.options["--prop"] = "hess"
    calc.run()
    if return_calc:
        return calc.conformers, calc
    else:
        return calc.conformers


def protonate(
    input_geometry: Geometry,
    solvation: str | None = None,
    method: int = 2,
    n_proc: int | None = None,
    return_calc: bool = False,
) -> list[dict]:
    """Screen possible protonation sites and return set of tautomer Geometries and energies.

    The returned tautomers are ordered from lowest to highest energy.
    """
    method_flag = f"gfn{method}"
    calc = Calculation(
        program="crest",
        input_geometry=input_geometry,
        runtype="protonate",
        options={
            "xnam": XTB_BIN,
            method_flag: True,
            "alpb": solvation,
            "T": n_proc if n_proc else config["n_proc"],
        },
    )
    calc.run()
    if return_calc:
        return calc.tautomers, calc
    else:
        return calc.tautomers


def deprotonate(
    input_geometry: Geometry,
    solvation: str | None = None,
    method: int = 2,
    n_proc: int | None = None,
    return_calc: bool = False,
) -> list[dict]:
    """Screen possible deprotonation sites and return set of tautomer Geometries and energies.

    The returned tautomers are ordered from lowest to highest energy.
    """
    method_flag = f"gfn{method}"
    calc = Calculation(
        program="crest",
        input_geometry=input_geometry,
        runtype="deprotonate",
        options={
            "xnam": XTB_BIN,
            method_flag: True,
            "alpb": solvation,
            "T": n_proc if n_proc else config["n_proc"],
        },
    )
    calc.run()
    if return_calc:
        return calc.tautomers, calc
    else:
        return calc.tautomers
