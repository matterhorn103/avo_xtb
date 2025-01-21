# SPDX-FileCopyrightText: 2024 Matthew J. Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

"""
Provides a simpler function-based calculation API.

The function-based API returns just the values of interest for a given geometry in a
quick and intuitive fashion, without the user having to worry about `Calculation`
objects.
"""

from .calc import Calculation
from .geometry import Geometry


def energy(
    input_geometry: Geometry,
    solvation: str | None = None,
    method: int | None = None,
    n_proc: int | None = None,
    options: dict | None = None,
) -> float:
    """Calculate the energy in hartree of the given geometry."""

    calc = Calculation.sp(
        input_geometry,
        solvation=solvation,
        method=method,
        n_proc=n_proc,
        orbitals=False,
        options=options,
    )
    calc.run()
    return calc.energy


def optimize(
    input_geometry: Geometry,
    level: str | None = None,
    solvation: str | None = None,
    method: int | None = None,
    n_proc: int | None = None,
    options: dict | None = None,
) -> Geometry:
    """Optimize the geometry, starting from the provided initial geometry, and return
    the optimized geometry."""

    calc = Calculation.opt(
        input_geometry,
        level=level,
        solvation=solvation,
        method=method,
        n_proc=n_proc,
        options=options,
    )
    calc.run()
    # Check for convergence
    # TODO
    # Will need to look for "FAILED TO CONVERGE"
    return calc.output_geometry


def frequencies(
    input_geometry: Geometry,
    solvation: str | None = None,
    method: int | None = None,
    n_proc: int | None = None,
    options: dict | None = None,
) -> list[dict]:
    """Calculate vibrational frequencies and return results as a list of dicts."""

    calc = Calculation.hess(
        input_geometry,
        solvation=solvation,
        method=method,
        n_proc=n_proc,
        options=options,
    )
    calc.run()
    return calc.frequencies


def smartopt(
    input_geometry: Geometry,
    level: str | None = None,
    solvation: str | None = None,
    method: int | None = None,
    n_proc: int | None = None,
    options: dict | None = None,
) -> Geometry:
    """Optimize the geometry repeatedly until a minimum is reached.
    
    If xtb is run with the `ohess` runtype (an optimization and subsequent frequency
    calculation) and the program detects one or more imaginary frequencies in the
    result, it distorts the optimized geometry away from the stationary point and
    recommends to restart the calculation from that distorted geometry.

    The `smartopt` function takes advantage of this and does that restart automatically,
    and will continue to restart the optimizations until a minimum is reached.

    Be aware that this could in theory get stuck in an endless loop if xtb never finds
    a minimum, though in practice it seems to only need at maximum a couple of
    iterations.
    """

    calc = Calculation.ohess(
        input_geometry=input_geometry,
        solvation=solvation,
        method=method,
        level=level,
        n_proc=n_proc,
        options=options,
    )
    calc.run()

    # Check for distorted geometry
    # (Generated automatically by xtb if result had negative frequency)
    # If found, rerun
    distorted_geom_file = calc.output_file.with_name("xtbhess.xyz")
    while distorted_geom_file.exists():
        calc = Calculation.ohess(
            input_geometry=Geometry.load_file(
                distorted_geom_file, charge=input_geometry.charge, spin=input_geometry.spin
            ),
            solvation=solvation,
            method=method,
            level=level,
            n_proc=n_proc,
            options=options,
        )
        calc.run()

    return calc.output_geometry


def orbitals(
    input_geometry: Geometry,
    solvation: str | None = None,
    method: int | None = None,
    n_proc: int | None = None,
    options: dict | None = None,
    ) -> str:
    """Calculate molecular orbitals for given geometry.

    Returns a string of the Molden-format output file, which contains principally the
    GTO and MO information.
    """

    calc = Calculation.sp(
        input_geometry=input_geometry,
        solvation=solvation,
        method=method,
        n_proc=n_proc,
        molden=True,
        options=options,
    )
    calc.run()
    return calc.output_molden


def conformers(
    input_geometry: Geometry,
    solvation: str | None = None,
    method: int | None = None,
    ewin: int | float = 6,
    hess: bool = False,
    n_proc: int | None = None,
    options: dict | None = None,
) -> list[dict]:
    """Simulate a conformer ensemble and return set of conformer Geometries and energies.

    The returned conformers are ordered from lowest to highest energy.

    All conformers within <ewin> kcal/mol are kept.
    If hess=True, vibrational frequencies are calculated and the conformers reordered by Gibbs energy.
    """

    calc = Calculation.v3(
        input_geometry=input_geometry,
        solvation=solvation,
        method=method,
        ewin=ewin,
        hess=hess,
        n_proc=n_proc,
        options=options,
    )
    calc.run()
    return calc.conformers


def tautomerize(
    input_geometry: Geometry,
    solvation: str | None = None,
    method: int | None = None,
    n_proc: int | None = None,
    options: dict | None = None,
) -> list[dict]:
    """Sample prototropic tautomers and return set of tautomer Geometries and energies.

    The returned tautomers are ordered from lowest to highest energy.
    """

    calc = Calculation.tautomerize(
        input_geometry=input_geometry,
        solvation=solvation,
        method=method,
        n_proc=n_proc,
        options=options,
    )
    calc.run()
    return calc.tautomers


def protonate(
    input_geometry: Geometry,
    solvation: str | None = None,
    method: int | None = None,
    n_proc: int | None = None,
    options: dict | None = None,
) -> list[dict]:
    """Screen possible protonation sites and return set of tautomer Geometries and energies.

    The returned tautomers are ordered from lowest to highest energy.
    """
    
    calc = Calculation.protonate(
        input_geometry=input_geometry,
        solvation=solvation,
        method=method,
        n_proc=n_proc,
        options=options,
    )
    calc.run()
    return calc.tautomers


def deprotonate(
    input_geometry: Geometry,
    solvation: str | None = None,
    method: int | None = None,
    n_proc: int | None = None,
    options: dict | None = None,
) -> list[dict]:
    """Screen possible deprotonation sites and return set of tautomer Geometries and energies.

    The returned tautomers are ordered from lowest to highest energy.
    """
    
    calc = Calculation.deprotonate(
        input_geometry=input_geometry,
        solvation=solvation,
        method=method,
        n_proc=n_proc,
        options=options,
    )
    calc.run()
    return calc.tautomers


def solvate(
    solute_geometry: Geometry,
    solvent_geometry: Geometry,
    nsolv: int,
    method: int | None = None,
    n_proc: int | None = None,
    options: dict | None = None,
) -> Geometry:
    """Grow a solvent shell around a solute for a total of `nsolv` solvent molecules.

    Note that non-zero charge and spin on the solvent `Geometry` will not be passed to
    CREST.
    """

    calc = Calculation.qcg(
        solute_geometry=solute_geometry,
        solvent_geometry=solvent_geometry,
        nsolv=nsolv,
        method=method,
        n_proc=n_proc,
        options=options,
    )
    calc.run()
    return calc.output_geometry
