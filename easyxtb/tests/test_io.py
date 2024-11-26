# SPDX-FileCopyrightText: 2024 Matthew J. Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

import json
from pathlib import Path

from easyxtb import Geometry
from . import equal_geom


files_dir = Path(__file__).parent / "files/input"
input_files = [
    "acetic_acid",
    "acetone",
    "benzene",
    "benzoate",
    "bu4n",
    "tempo",
]

def test_parse_xyz():
    for mol in input_files:
        with open(files_dir / f"{mol}.xyz", encoding="utf-8") as f:
            xyz = f.read()
        Geometry.from_xyz(xyz.split("\n"))

def test_parse_cjson():
    for mol in input_files:
        with open(files_dir / f"{mol}.cjson", encoding="utf-8") as f:
            cjson = json.load(f)
        Geometry.from_cjson(cjson)

def test_open_xyz():
    for mol in input_files:
        Geometry.from_file(files_dir / f"{mol}.xyz")

def test_open_cjson():
    for mol in input_files:
        Geometry.from_file(files_dir / f"{mol}.cjson")

def test_xyz_cjson_coords_equivalence():
    for mol in input_files:
        print(mol)
        xyz_geom = Geometry.from_file(files_dir / f"{mol}.xyz")
        cjson_geom = Geometry.from_file(files_dir / f"{mol}.cjson")
        assert equal_geom(xyz_geom, cjson_geom, precision=14)

def test_default_xyz_charge_spin():
    for mol in input_files:
        with open(files_dir / f"{mol}.xyz", encoding="utf-8") as f:
            xyz = f.read()
        g = Geometry.from_xyz(xyz.split("\n"))
        assert g.charge == 0
        assert g.spin == 0

def test_specify_xyz_charge():
    benzoate = Geometry.from_file(files_dir / "benzoate.xyz", charge=-1)
    assert benzoate.charge == -1

def test_specify_xyz_spin():
    tempo = Geometry.from_file(files_dir / "tempo.xyz", spin=1)
    assert tempo.spin == 1

def test_default_cjson_charge_spin():
    acetone = Geometry.from_file(files_dir / "acetone_bare.cjson")
    benzoate = Geometry.from_file(files_dir / "benzoate_bare.cjson")
    assert acetone.charge == 0
    assert acetone.spin == 0
    assert benzoate.charge == 0
    assert benzoate.spin == 0

def test_parsed_cjson_charge_spin():
    acetone = Geometry.from_file(files_dir / "acetone.cjson")
    benzoate = Geometry.from_file(files_dir / "benzoate.cjson")
    tempo = Geometry.from_file(files_dir / "tempo.cjson")
    assert acetone.charge == 0
    assert acetone.spin == 0
    assert benzoate.charge == -1
    assert benzoate.spin == 0
    assert tempo.charge == 0
    assert tempo.spin == 1

def test_override_cjson_charge_spin():
    acetone = Geometry.from_file(files_dir / "acetone.cjson", charge=2, spin=5)
    assert acetone.charge == 2
    assert acetone.spin == 5

def test_generate_xyz():
    benzene = Geometry.from_file(files_dir / "benzene.xyz")
    benzene.to_xyz()

def test_generate_cjson():
    benzene = Geometry.from_file(files_dir / "benzene.cjson")
    benzene.to_cjson()

def test_write_xyz(tmp_path):
    acetic_acid = Geometry.from_file(files_dir / "acetic_acid.xyz")
    acetic_acid.write_xyz(tmp_path / "acetic_acid_out.xyz")

def test_write_cjson(tmp_path):
    acetic_acid = Geometry.from_file(files_dir / "acetic_acid.cjson")
    acetic_acid.write_cjson(tmp_path / "acetic_acid_out.cjson")

def test_xyz_roundtrip():
    bu4n_file = files_dir / "bu4n.xyz"
    with open(bu4n_file, encoding="utf-8") as f:
        bu4n_lines = f.read().splitlines()
    bu4n = Geometry.from_file(bu4n_file)
    # Compare agnostic wrt the number of spaces used
    assert str(bu4n.to_xyz()).split() == str(bu4n_lines).split()

def test_cjson_roundtrip():
    bu4n_file = files_dir / "bu4n_chrg_spin.cjson"
    with open(bu4n_file, encoding="utf-8") as f:
        bu4n_original = json.load(f)
    bu4n = Geometry.from_file(bu4n_file)
    bu4n_cjson_new = bu4n.to_cjson()
    assert bu4n_cjson_new == bu4n_original

def test_cjson_read_write_roundtrip(tmp_path):
    bu4n_file = files_dir / "bu4n_chrg_spin.cjson"
    with open(bu4n_file, encoding="utf-8") as f:
        bu4n_string_original = f.read()
    bu4n = Geometry.from_file(bu4n_file)
    bu4n.write_cjson(tmp_path / "bu4n_chrg_spin_out.cjson")
    with open(tmp_path / "bu4n_chrg_spin_out.cjson", encoding="utf-8") as f:
        bu4n_string_new = f.read()
    assert bu4n_string_original == bu4n_string_new
