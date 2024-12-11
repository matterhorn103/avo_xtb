# avo_xtb
`avo_xtb` is a plugin for Avogadro 2 that provides an in-app interface to the xtb program for quick and accurate calculations, as well as the CREST program for extended functionality.

[`xtb`](https://github.com/grimme-lab/xtb) is developed by the Grimme group in Bonn and carries out semi-empirical quantum mechanical calculations using the group's e**x**tended **T**ight-**B**inding methods, referred to as "GFNn-xTB".

These methods provide fast and reasonably accurate calculation of **G**eometries, **F**requencies, and **N**on-covalent interactions for molecular systems with up to roughly 1000 atoms, with broad coverage of the periodic table up to *Z* = 86 (radon).

[`crest`](https://github.com/crest-lab/crest) (Conformer–Rotamer Ensemble Sampling Tool) adds a variety of sampling procedures for several interesting applications including conformer searches, thermochemistry, and solvation.

## easyxtb

The Avogadro plugin is itself only a layer on top of the `easyxtb` Python package, which is written and maintained as part of this project.
`easyxtb` is published on the `PyPI` repository and can be used independently of the plugin from Python as an interface to `xtb` and `crest`.

For more details on using `easyxtb` via the Python API, see `easyxtb/README.md`.

## Capabilities

This plugin currently provides functionality to run the following calculation types and view the results directly in Avogadro:

### xtb
* single point energies
* geometry optimizations
* vibrational frequencies
* combined opt + freq with automatic restart for negative frequencies
* molecular orbitals

### CREST
* conformer searches
* protonation and deprotonation screening
* explicit solvent shell generation

### Run options
The following options for xtb and/or CREST can currently be configured in the plugin:
* number of parallel threads to use for calculations
* implicit solvation with the ALPB model
* choice of GFN-xTB parameterization
* optimization level
In addition, the pluding provides the possibility to specify extra command line options to pass to xtb and CREST in free form.

## Requirements

### xtb

Currently, the plugin does not download the `xtb` binary automatically, and it is not bundled with Avogadro. Instead, it must be obtained separately. There are five options that will make `xtb` visible to the plugin:
1. Use the "Get xtb..." function within Avogadro after installing this plugin and let the plugin take care of everything for you
2. Install xtb with `conda` from conda-forge and use Avogadro with the `conda` environment, either by setting it in the Python settings or by starting Avogadro with the environment activated
3. Manually download the `xtb` binary and put it into the system PATH
4. Manually download `xtb` and place it, or a link to it, entirely within the plugin's binary directory `<user data>/easyxtb/bin/` (see below for more information on where this is on your system) 
5. Manually download `xtb` and manually specify its location in the `Configure...` menu

### CREST

While `xtb` is cross-platform, `crest` is distributed only for Linux/UNIX systems. As a result, Windows and macOS users of the plugin will not have the calculations that rely on CREST available to them in the Avogadro interface.

`crest` can be made visible to the plugin in the same ways as for `xtb` listed above.
If it is not in `$PATH`, the `crest` binary, or a link to it, should be located at `<user data>/easyxtb/bin/crest`.
The "Get xtb..." option within Avogadro will also download `crest` on supported operating systems (only Linux at time of writing).

## Data location

The core package that provides the calculation framework uses a central location to run its calculations, store its configuration, and save its log file.
This location is `<user data>/easyxtb`, where `<user data>` is OS-dependent:

- Windows: `$USER_HOME\AppData\Local\easyxtb`
- macOS: `~/Library/Application Support/easyxtb`
- Linux: `~/.local/share/easyxtb`

Additionally, if the environment variable `XDG_DATA_HOME` is set its value will be respected and takes precedence over the above paths (on all OSes).

Normally calculations are run in a subfolder at this location, but this can be customized in the plugin's configuration dialog.

## Disclaimer

`xtb` and `crest` are distributed by the Grimme group under the LGPL license v3.
The authors of Avogadro and avo_xtb bear no responsibility for xtb or CREST or the contents of the respective repositories.
Source code for the programs is available at the repositories linked above.

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
