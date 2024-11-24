# SPDX-FileCopyrightText: 2024 Matthew J. Milner <matterhorn103@proton.me>
# SPDX-License-Identifier: BSD-3-Clause

import json
from pathlib import Path

from easyxtb import Geometry, Atom


files_dir = Path(__file__).parent / "files"
# These raw files are as produced by Avogadro nightlies as of 2024-11-24 (1.99-based)
raw_files = [
    "acetic_acid_raw",
    "acetone_raw",
    "benzene_raw",
    "benzoate_raw",
    "me4n_raw",
    "tempo_raw",
]

def test_parse_xyz():
    for filename in raw_files:
        with open(files_dir / f"{filename}.xyz", encoding="utf-8") as f:
            xyz = f.read()
        Geometry.from_xyz(xyz.split("\n"))

def test_parse_cjson():
    for filename in raw_files:
        with open(files_dir / f"{filename}.cjson", encoding="utf-8") as f:
            cjson = json.load(f)
        Geometry.from_cjson(cjson)

def test_open_xyz():
    for filename in raw_files:
        Geometry.from_file(files_dir / f"{filename}.xyz")

def test_open_cjson():
    for filename in raw_files:
        Geometry.from_file(files_dir / f"{filename}.cjson")

def round_atom_coordinates(atoms: list[Atom], precision: int = 10) -> list[Atom]:
    # Often have to account for difference in precision between formats or sources
    rounded_atoms = []
    for atom in atoms:
        rounded_atoms.append(
            Atom(
                atom.element,
                round(atom.x, precision),
                round(atom.y, precision),
                round(atom.z, precision),
            )
        )
    return rounded_atoms

def test_xyz_cjson_coords_equivalence():
    for filename in raw_files:
        xyz_geom = Geometry.from_file(files_dir / f"{filename}.xyz")
        cjson_geom = Geometry.from_file(files_dir / f"{filename}.cjson")
        rounded_xyz_atoms = round_atom_coordinates(xyz_geom.atoms, 10)
        rounded_cjson_atoms = round_atom_coordinates(cjson_geom.atoms, 10)
        assert rounded_xyz_atoms == rounded_cjson_atoms

def test_default_xyz_charge_multiplicity():
    for filename in raw_files:
        with open(files_dir / f"{filename}.xyz", encoding="utf-8") as f:
            xyz = f.read()
        g = Geometry.from_xyz(xyz.split("\n"))
        assert g.charge == 0
        assert g.multiplicity == 1

def test_specify_xyz_charge():
    benzoate = Geometry.from_file(files_dir / "benzoate_raw.xyz", charge=-1)
    assert benzoate.charge == -1

def test_specify_xyz_multiplicity():
    tempo = Geometry.from_file(files_dir / "tempo_raw.xyz", multiplicity=2)
    assert tempo.multiplicity == 2

def test_default_cjson_charge_multiplicity():
    acetone = Geometry.from_file(files_dir / "acetone_bare.cjson")
    benzoate = Geometry.from_file(files_dir / "benzoate_bare.cjson")
    assert acetone.charge == 0
    assert acetone.multiplicity == 1
    assert benzoate.charge == 0
    assert benzoate.multiplicity == 1

def test_parsed_cjson_charge_multiplicity():
    acetone = Geometry.from_file(files_dir / "acetone_raw.cjson")
    benzoate = Geometry.from_file(files_dir / "benzoate_raw.cjson")
    tempo = Geometry.from_file(files_dir / "tempo_raw.cjson")
    assert acetone.charge == 0
    assert acetone.multiplicity == 1
    assert benzoate.charge == -1
    assert benzoate.multiplicity == 1
    assert tempo.charge == 0
    assert tempo.multiplicity == 2

def test_override_cjson_charge_multiplicity():
    acetone = Geometry.from_file(files_dir / "acetone_raw.cjson", charge=2, multiplicity=5)
    assert acetone.charge == 2
    assert acetone.multiplicity == 5

def test_generate_xyz():
    benzene = Geometry.from_file(files_dir / "benzene_raw.xyz")
    benzene.to_xyz()

def test_generate_cjson():
    benzene = Geometry.from_file(files_dir / "benzene_raw.cjson")
    benzene.to_cjson()

def test_write_xyz(tmp_path):
    acetic_acid = Geometry.from_file(files_dir / "acetic_acid_raw.xyz")
    acetic_acid.write_xyz(tmp_path / "acetic_acid_raw_out.xyz")

def test_write_cjson(tmp_path):
    acetic_acid = Geometry.from_file(files_dir / "acetic_acid_raw.cjson")
    acetic_acid.write_cjson(tmp_path / "acetic_acid_raw_out.cjson")

def test_xyz_roundtrip():
    me4n_file = files_dir / "me4n_raw.xyz"
    with open(me4n_file, encoding="utf-8") as f:
        me4n_lines = f.read().splitlines()
    me4n = Geometry.from_file(me4n_file)
    # Compare agnostic wrt the number of spaces used
    assert str(me4n.to_xyz()).split() == str(me4n_lines).split()

def test_cjson_roundtrip():
    me4n_file = files_dir / "me4n_chrg_spin.cjson"
    with open(me4n_file, encoding="utf-8") as f:
        me4n_original = json.load(f)
    me4n = Geometry.from_file(me4n_file)
    me4n_cjson_new = me4n.to_cjson()
    assert me4n_cjson_new == me4n_original

def test_cjson_read_write_roundtrip(tmp_path):
    me4n_file = files_dir / "me4n_chrg_spin.cjson"
    with open(me4n_file, encoding="utf-8") as f:
        me4n_string_original = f.read()
    me4n = Geometry.from_file(me4n_file)
    me4n.write_cjson(tmp_path / "me4n_chrg_spin_out.cjson")
    with open(tmp_path / "me4n_chrg_spin_out.cjson", encoding="utf-8") as f:
        me4n_string_new = f.read()
    assert me4n_string_original == me4n_string_new
