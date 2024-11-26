# easyxtb

`easyxtb` is an unofficial API for the xtb and CREST semi-empirical quantum chemistry programs with an emphasis on intuitive and straightforward usage.

It forms the basis for `avo_xtb`, a plugin for the 3D chemical visualization software [Avogadro 2](https://two.avogadro.cc) that provides an in-app interface to the xtb program for quick and accurate calculations, as well as the CREST program for extended functionality.

The Python package `easyxtb` can be used independently of `avo_xtb` as an interface to launch calculations and process their results from Python.

[`xtb`](https://github.com/grimme-lab/xtb) is developed by the Grimme group in Bonn and carries out semi-empirical quantum mechanical calculations using the group's e**x**tended **T**ight-**B**inding methods, referred to as "GFNn-xTB".

These methods provide fast and reasonably accurate calculation of **G**eometries, **F**requencies, and **N**on-covalent interactions for molecular systems with up to roughly 1000 atoms, with broad coverage of the periodic table up to *Z* = 86 (radon).

[`crest`](https://github.com/crest-lab/crest) (Conformer–Rotamer Ensemble Sampling Tool) adds a variety of sampling procedures for several interesting applications including conformer searches, thermochemistry, and solvation.

## Usage

Full documentation is a work in progress, but to demonstrate basic usage:

To load a geometry (XYZ and CJSON files are supported currently):

```python
>>> from pathlib import Path
>>> import py_xtb
>>> py_xtb.XTB_BIN = Path.home() / ".local/bin/xtb"
>>> input_geom = py_xtb.Geometry.from_file(Path.home() / "calcs/benzoic_acid.xyz")
>>> input_geom
<py_xtb.geometry.Geometry object at 0x7ff91fdb15d0>
>>> input_geom.atoms
[Atom(element='C', x=-3.61652, y=0.64945, z=-0.0), Atom(element='C', x=-3.59105, y=-1.15881, z=-0.0), Atom(element='C', x=-0.43296, y=-1.32436, z=-1e-05), ..., Atom(element='O', x=1.54084, y=3.42551, z=-1e-05), Atom(element='O', x=2.9034, y=0.39476, z=1e-05), Atom(element='H', x=2.60455, y=-0.50701, z=2e-05)]
>>> for atom in input_geom:
...     print(atom)
... 
Atom(element='C', x=-3.61652, y=0.64945, z=-0.0)
Atom(element='C', x=-3.59105, y=-1.15881, z=-0.0)
... # Truncated for brevity
Atom(element='O', x=2.9034, y=0.39476, z=1e-05)
Atom(element='H', x=2.60455, y=-0.50701, z=2e-05)
```

Charge and spin are picked up automatically from a CJSON file, but for XYZ files or for overriding they can be specified:

```python
>>> acetate_anion = py_xtb.Geometry.from_file(Path.home() / "calcs/acetate.xyz", charge=-1)
```

Note that `easyxtb` follows the convention used by `xtb` itself, where `spin` is the number of unpaired electrons.

The package provides a function API for basic xtb calculation types (`energy`, `optimize`, `frequencies`, `opt_freq`, `orbitals`):

```python
>>> optimized = py_xtb.calculate.optimize(input_geom, solvation="water", method=2, level="normal")
>>> for atom in optimized:
...     print(atom)
... 
Atom(element='C', x=-2.94841377173243, y=0.53595421697827, z=-0.00205114575446)
Atom(element='C', x=-2.96353116164446, y=-0.85021326429608, z=-0.00028605784754)
... # Truncated for brevity
Atom(element='O', x=1.83119245847571, y=0.4663499792285, z=-0.00384872174663)
Atom(element='H', x=1.55896002888703, y=-0.46876579604809, z=-0.00948378184114)
```

For greater control and for runtypes or command line options that don't yet have support in the API the `Calculation` object can be used:

```python
>>> freq_calc = py_xtb.Calculation(program="xtb", runtype="hess", options={"solvation": "water"})
>>> freq_calc.input_geometry = input_geom
>>> freq_calc.run()
>>> freq_calc.energy
-24.418716794336
>>> freq_calc.output_geometry
<py_xtb.geometry.Geometry object at 0x7ff91fdb15d0>
>>> freq_calc.frequencies
[{'mode': 1, 'symmetry': 'a', 'frequency': -816.7902, 'reduced_mass': 12.1428, 'ir_intensity': 7.2604, 'raman_scattering_activity': 0.0, 'eigenvectors': [[-0.26, -0.46, 0.0], [-0.24, 0.43, -0.0], [-0.05, -0.05, 0.0], [0.08, 0.3, -0.0], [0.42, 0.02, -0.0], [-0.02, 0.03, -0.0], [0.24, -0.09, -0.0], [0.0, -0.02, 0.0], [-0.26, 0.1, 0.0], [0.05, 0.01, -0.0], [-0.02, -0.03, 0.0], [0.0, -0.21, 0.0], [0.05, 0.0, -0.0], [-0.02, 0.01, -0.0]]}, {'mode': 2, 'symmetry': 'a', 'frequency': -759.3794, 'reduced_mass': 12.9124, 'ir_intensity': 17.3638, 'raman_scattering_activity': 0.0, 'eigenvectors': [[0.12, 0.19, -0.0], [0.15, -0.32, 0.0], [0.07, 0.18, -0.0], [0.12, 0.58, -0.0], [0.01, -0.11, 0.0], [0.01, -0.03, 0.0], [-0.29, 0.05, 0.0], [-0.02, 0.01, 0.0], [-0.32, -0.02, -0.0], [0.02, -0.03, -0.0], [0.01, 0.01, -0.0], [-0.01, -0.47, 0.0], [0.13, -0.0, -0.0], [-0.03, 0.02, 0.0]]}, ..., {'mode': 36, 'symmetry': 'a', 'frequency': 3752.5636, 'reduced_mass': 1.893, 'ir_intensity': 79.5584, 'raman_scattering_activity': 0.0, 'eigenvectors': [[-0.0, -0.0, 0.0], [0.0, -0.0, 0.0], [0.0, 0.0, -0.0], [-0.0, 0.0, 0.0], [-0.0, 0.0, -0.0], [-0.0, 0.0, -0.0], [0.0, 0.0, 0.0], [-0.0, 0.0, 0.0], [0.0, 0.0, -0.0], [0.0, 0.0, -0.0], [-0.0, 0.0, -0.0], [-0.0, -0.0, 0.0], [0.08, 0.23, -0.0], [-0.31, -0.92, 0.0]]}]
```

We were returned some negative frequencies!
The xtb team recommend generally using the `ohess` (optimization followed by a frequency calculation) as, in the case of negative frequencies, xtb will produce a distorted geometry along the imaginary mode.
The `opt_freq()` calculation function takes advantage of this and will continue reoptimizing using these distorted geometries until a minimum is reached, so is more reliable in getting what we want:

```python
>>> output_geom, output_freqs, calc = py_xtb.calculate.opt_freq(input_geom, solvation="water", return_calc=True)
>>> output_freqs[0]
{'mode': 1, 'symmetry': 'a', 'frequency': 70.0622, 'reduced_mass': 13.4154, 'ir_intensity': 6.422, 'raman_scattering_activity': 0.0, 'eigenvectors': [[0.0, 0.0, -0.28], [-0.0, 0.0, -0.0], [-0.0, -0.0, 0.25], [0.0, -0.0, 0.04], [0.0, -0.0, -0.24], [-0.0, 0.0, -0.0], [-0.0, 0.0, 0.29], [-0.0, 0.0, 0.15], [0.0, -0.0, 0.02], [0.0, -0.0, -0.12], [0.0, 0.0, -0.15], [0.0, -0.0, 0.55], [0.0, 0.01, -0.56], [0.0, 0.0, -0.19]]}
```

The geometries can be converted back to XYZ or CJSON formats, or saved to file:

```python
>>> output_geom.to_xyz()
['14', ' energy: -25.558538770724 gnorm: 0.000926226194 xtb: 6.7.1 (edcfbbe)', 'C        -2.94841     0.53597    -0.00204', 'C        -2.96354    -0.85020    -0.00027', 'C        -0.61077    -0.84138     0.00148', 'C         0.75088     1.26262     0.00405', 'C        -1.75577     1.23036    -0.00190', 'H        -3.89917    -1.39047     0.00050', 'C        -1.76452    -1.56433     0.00117', 'H        -1.76882    -2.64357     0.00283', 'C        -0.54492     0.52708     0.00053', 'H        -1.70901     2.30959    -0.00318', 'H        -3.88278     1.07775    -0.00326', 'O         0.84510     2.45868     0.01349', 'O         1.83119     0.46634    -0.00386', 'H         1.55896    -0.46877    -0.00949']
>>> output_geom.to_cjson()
{'atoms': {'coords': {'3d': [-2.94841097258746, 0.53596965124863, -0.00204178926542, -2.96353561428538, -0.85019774776951, -0.0002742292702, -0.61076575425764, -0.84137850926872, 0.00147639902781, 0.75088171422694, 1.2626220330939, 0.00405051293617, -1.75577241044775, 1.23035899741552, -0.00189846159875, -3.89916811270068, -1.39047034080804, 0.00049537269594, -1.76451828574256, -1.56433051119015, 0.00116984833688, -1.76882023929805, -2.64357304665774, 0.00283010066276, -0.54491722564374, 0.52708246765258, 0.00052577760818, -1.70901066150243, 2.30958748867245, -0.00317692528336, -3.88277644809706, 1.07774511697242, -0.00326302099431, 0.84510262816245, 2.45867627843098, 0.01348592446867, 1.83119488680479, 0.46634038440289, -0.00385592774839, 1.55895754130232, -0.46877397528872, -0.00948840548749]}, 'elements': {'number': [6, 6, 6, 6, 6, 1, 6, 1, 6, 1, 1, 8, 8, 1]}}}
>>> output_geom.to_file(Path.home() / "calcs/optimized_benzoic_acid.xyz")
```

## Requirements

### xtb

Only tested for `xtb >= 6.7`.

The `xtb` binary is not bundled with the package.
Instead, it must be obtained separately.

The location of `xtb` can be set from Python code simply by setting `easyxtb.XTB_BIN` to an appropriate `pathlib.Path` object.

An `xtb` binary will also be picked up automatically by `easyxtb` if located in one of the following locations:
1. The system or user PATH
2. Within the `easyxtb` binary directory at `<user data>/easyxtb/bin/xtb` (see below for more information on where this is on your system)
3. Within the folder it is distributed in under the `easyxtb` binary directory, which would thus currently be at `<user data>/easyxtb/bin/xtb-dist/bin/xtb`
4. Any other location but with a link to it from `<user data>/easyxtb/bin/xtb`

### CREST

Only tested for `crest >= 3.0`.

While `xtb` is cross-platform, `crest` is currently distributed only for Linux/UNIX systems.

`crest` can be made visible to the plugin in the same ways as for `xtb` listed above.
If it is not in `$PATH`, the `crest` binary, or link to it, should be located at `<user data>/easyxtb/bin/crest`.

## Data location

`easyxtb` uses a central location to run its calculations, store its configuration, and save its log file.
This location is `<user data>/easyxtb`, where `<user data>` is OS-dependent:

- Windows: `$USER_HOME\AppData\Local\easyxtb`
- macOS: `~/Library/Application Support/easyxtb`
- Linux: `~/.local/share/easyxtb`

Additionally, if the environment variable `XDG_DATA_HOME` is set its value will be respected and takes precedence over the above paths (on all OSes).

## Disclaimer

`xtb` and `crest` are distributed by the Grimme group under the LGPL license v3. The authors of `easyxtb`, `avo_xtb`, and Avogadro bear no responsibility for xtb or CREST or the contents of the respective repositories. Source code for the programs is available at the repositories linked above.

## Cite

General reference to `xtb` and the implemented GFN methods:
* C. Bannwarth, E. Caldeweyher, S. Ehlert, A. Hansen, P. Pracht, J. Seibert, S. Spicher, S. Grimme
  *WIREs Comput. Mol. Sci.*, **2020**, 11, e01493.
  DOI: [10.1002/wcms.1493](https://doi.org/10.1002/wcms.1493)

For GFN2-xTB (default method):
* C. Bannwarth, S. Ehlert and S. Grimme., *J. Chem. Theory Comput.*, **2019**, 15, 1652-1671. DOI: [10.1021/acs.jctc.8b01176](https://dx.doi.org/10.1021/acs.jctc.8b01176)

For CREST:
* P. Pracht, S. Grimme, C. Bannwarth, F. Bohle, S. Ehlert, G. Feldmann, J. Gorges, M. Müller, T. Neudecker, C. Plett, S. Spicher, P. Steinbach, P. Wesołowski, F. Zeller, *J. Chem. Phys.*, **2024**, *160*, 114110. DOI: [10.1063/5.0197592](https://doi.org/10.1063/5.0197592)
* P. Pracht, F. Bohle, S. Grimme, *Phys. Chem. Chem. Phys.*, **2020**, 22, 7169-7192. DOI: [10.1039/C9CP06869D](https://dx.doi.org/10.1039/C9CP06869D)

See the xtb and CREST GitHub repositories for other citations.
