# SPDX-FileCopyrightText: 2024 Matthew J. Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path

from easyxtb import Geometry, calculate, parse
from . import equal_geom


input_dir = Path(__file__).parent / "files/input"
results_dir = Path(__file__).parent / "files/output"
# Note that the input structures for acetic acid and acetone both optimize to a saddle
# point, not a minimum!
mols = [
    "acetic_acid",
    "acetone",
    "benzene",
    "benzoate",
    "bu4n",
    "tempo",
]

def test_opt_neutral_singlet():
    for mol in ["acetic_acid", "acetone", "benzene"]:
        in_geom = Geometry.from_file(input_dir / f"{mol}.cjson")
        out_geom = calculate.optimize(in_geom)
        ref_geom = Geometry.from_file(results_dir / f"{mol}_opt.xyz")
        print(f"Testing {mol}:")
        assert equal_geom(out_geom, ref_geom)
        print("  Success")

def test_opt_charged():
    for mol in ["benzoate", "bu4n"]:
        in_geom = Geometry.from_file(input_dir / f"{mol}.cjson")
        out_geom = calculate.optimize(in_geom)
        ref_geom = Geometry.from_file(results_dir / f"{mol}_opt.xyz")
        print(f"Testing {mol}:")
        assert equal_geom(out_geom, ref_geom)
        print("  Success")

def test_opt_doublet():
    for mol in ["tempo"]:
        in_geom = Geometry.from_file(input_dir / f"{mol}.cjson")
        out_geom = calculate.optimize(in_geom)
        ref_geom = Geometry.from_file(results_dir / f"{mol}_opt.xyz")
        print(f"Testing {mol}:")
        assert equal_geom(out_geom, ref_geom)
        print("  Success")

def test_freq_neutral_singlet():
    for mol in ["acetic_acid", "acetone", "benzene"]:
        opt_geom = Geometry.from_file(results_dir / f"{mol}_opt.xyz")
        freqs = calculate.frequencies(opt_geom)
        with open(results_dir / f"{mol}_g98.out", encoding="utf-8") as f:
            ref_freqs = parse.parse_g98_frequencies(f.read())
        print(f"Testing {mol}:")
        assert freqs == ref_freqs
        print("  Success")

def test_freq_anion():
    for mol in ["benzoate"]:
        opt_geom = Geometry.from_file(results_dir / f"{mol}_opt.xyz", charge=-1)
        freqs = calculate.frequencies(opt_geom)
        with open(results_dir / f"{mol}_g98.out", encoding="utf-8") as f:
            ref_freqs = parse.parse_g98_frequencies(f.read())
        print(f"Testing {mol}:")
        assert freqs == ref_freqs
        print("  Success")

def test_freq_cation():
    for mol in ["bu4n"]:
        opt_geom = Geometry.from_file(results_dir / f"{mol}_opt.xyz", charge=1)
        freqs = calculate.frequencies(opt_geom)
        with open(results_dir / f"{mol}_g98.out", encoding="utf-8") as f:
            ref_freqs = parse.parse_g98_frequencies(f.read())
        print(f"Testing {mol}:")
        assert freqs == ref_freqs
        print("  Success")

def test_freq_doublet():
    for mol in ["tempo"]:
        opt_geom = Geometry.from_file(results_dir / f"{mol}_opt.xyz", spin=1)
        freqs = calculate.frequencies(opt_geom)
        with open(results_dir / f"{mol}_g98.out", encoding="utf-8") as f:
            ref_freqs = parse.parse_g98_frequencies(f.read())
        print(f"Testing {mol}:")
        assert freqs == ref_freqs
        print("  Success")
