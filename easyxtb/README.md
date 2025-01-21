# easyxtb

`easyxtb` is an unofficial Python API for the xtb and CREST semi-empirical quantum chemistry programs with an emphasis on intuitive and straightforward usage.

[`xtb`](https://github.com/grimme-lab/xtb) is developed by the Grimme group in Bonn and carries out semi-empirical quantum mechanical calculations using the group's e**x**tended **T**ight-**B**inding methods, referred to as "GFNn-xTB".

These methods provide fast and reasonably accurate calculation of **G**eometries, **F**requencies, and **N**on-covalent interactions for molecular systems with up to roughly 1000 atoms, with broad coverage of the periodic table up to *Z* = 86 (radon).

[`crest`](https://github.com/crest-lab/crest) (Conformer–Rotamer Ensemble Sampling Tool) adds a variety of sampling procedures for several interesting applications including conformer searches, thermochemistry, and solvation.

`easyxtb` can be used as an interface to launch calculations and process their results.
By taking care of file I/O and command line invocation it aims to make it trivial to run xtb programmatically.
The package's design enables both straightforward acquisition of key results and full control over run options.

The `easyxtb` package also forms the basis for [`avo_xtb`](https://github.com/matterhorn103/avo_xtb), a plugin for the 3D chemical visualization software [Avogadro 2](https://two.avogadro.cc) that provides an in-app interface to the xtb program for quick and accurate calculations, as well as the CREST program for extended functionality.

## Usage

The package strives to make using xtb from Python as simple as possible and calculations can often be run as straightforwardly as:

```python
from pathlib import Path
import easyxtb

input_geom = easyxtb.Geometry.from_file(Path.home() / "calcs/benzoic_acid.xyz")
optimized = easyxtb.calculate.optimize(input_geom, level="normal", solvation="water")
```

An guide for [getting started](guide.md) and details of the API can be found in the [documentation](index.md).

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
