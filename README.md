# avo_xtb
`avo_xtb` is a plugin for Avogadro 2 that provides an in-app interface to the xtb program for quick and accurate calculations, as well as the CREST program for extended functionality.

[`xtb`](https://github.com/grimme-lab/xtb) is developed by the Grimme group in Bonn and carries out semi-empirical quantum mechanical calculations using the group's e**x**tended **T**ight-**B**inding methods, referred to as "GFNn-xTB".

These methods provide fast and reasonably accurate calculation of **G**eometries, **F**requencies, and **N**on-covalent interactions for molecular systems with up to roughly 1000 atoms, with broad coverage of the periodic table up to *Z* = 86 (radon).

[`crest`](https://github.com/crest-lab/crest) (Conformer–Rotamer Ensemble Sampling Tool) adds a variety of sampling procedures for several interesting applications including conformer searches, thermochemistry, and solvation.

## py-xtb

The Avogadro plugin is itself only a layer on top of the `py-xtb` Python package, which is written and maintained as part of this project.
`py-xtb` is published on the `PyPI` repository and can be used independently of the plugin from Python as an interface to `xtb` and `crest`.

For more details on the Python API, see `py-xtb/README.md`.

## Capabilities

This plugin currently provides functionality to run the following calculation types and view the results directly in Avogadro:

### xtb
* single point energies
* geometry optimizations
* vibrational frequencies
* molecular orbitals
* molecular dynamics

There is also the option to submit a custom command to `xtb`, permitting any calculation to be run, though the output is in this case only parsed for results of the basic calculation types.

### CREST
* conformer searches

## Requirements

### xtb

Currently, the plugin does not download the `xtb` binary automatically, and it is not bundled with Avogadro. Instead, it must be obtained separately. There are five options that will make `xtb` visible to the extension:
1. Install xtb with `conda` from conda-forge and use Avogadro with the `conda` environment, either by setting it in the Python settings or by starting Avogadro with the environment activated
2. Manually download the `xtb` binary and put it into the system PATH
3. Manually download `xtb` and place it entirely within the `<user data>/py-xtb/bin/` directory
4. Manually download `xtb` and manually specify its location in the `Configure...` menu
5. Use the "Get xtb..." function within Avogadro after installing this extension

### CREST

While `xtb` is cross-platform, `crest` is distributed only for Linux/UNIX systems. As a result, Windows and macOS users of the plugin will not have the calculations that rely on CREST available to them in the Avogadro interface.

`crest` can be made visible to the plugin in the same ways as for `xtb` listed above. If method 3 is used, `crest` should be located at `<user data>/py-xtb/bin/crest`. The "Get xtb..." option within Avogadro will also download `crest` on supported operating systems.

### Open Babel

The plugin also relies on Open Babel for conversion of output files to Avogadro's `cjson` format. The path to the `obabel` binary can be specified in the `Configure...` menu if it is not automatically detected.
* If you use Avogadro on Windows, macOS, or the AppImage or Flatpak on Linux, you have a recent build of `obabel` with CJSON support in the same folder as the Avogadro executable, and you should use that. The plugin should hopefully find it automatically.
* If you have obtained it from a distro's repositories, your version of `obabel` ***does not*** have the necessary CJSON support, and you will unfortunately have to compile it yourself from the [latest code](https://github.com/openbabel/openbabel).

## Disclaimer

`xtb` and `crest` are distributed by the Grimme group under the LGPL license v3. The authors of Avogadro and avo_xtb bear no responsibility for xtb or CREST or the contents of the respective repositories. Source code for the programs is available at the repositories linked above.

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
