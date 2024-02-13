# avo_xtb
This plugin adds an interface to the xtb program in Avogadro 2.

[`xtb`](https://github.com/grimme-lab/xtb) is developed by the Grimme group in Bonn and carries out semi-empirical quantum mechanical calculations using the group's e**x**tended **T**ight-**B**inding methods, referred to as "GFNn-xTB".

These methods provide fast and reasonably accurate calculation of **G**eometries, **F**requencies, and **N**on-covalent interactions for molecular systems with up to roughly 1000 atoms, with broad coverage of the periodic table up to *Z* = 86 (radon).

# Capabilities

This plugin currently provides functionality to run the following calculation types and view the results directly in Avogadro:
* single point energies
* geometry optimizations
* vibrational frequencies
* molecular orbitals
* molecular dynamics
* conformer searches (via [crest](https://github.com/crest-lab))

There is also the option to submit a custom command to `xtb`, permitting any calculation to be run, though the output is in this case only parsed for results of the basic calculation types.

# Requirements

### xtb

Currently, the plugin does not download the `xtb` binary automatically, and they are not bundled with Avogadro. `xtb` (and `crest` for conformer searches) must be obtained separately. There are five options that will make `xtb` visible to the extension:
1. Install xtb with `conda` from conda-forge and use Avogadro with the `conda` environment, either by setting it in the Python settings or by starting Avogadro with the environment activated
2. Manually download the `xtb` binary and put it into the system PATH
3. Manually download `xtb` and place it entirely within the `Avogadro/commands/avo_xtb/` directory
4. Manually download `xtb` and manually specify its location in the `Configure...` menu
5. Use the "Get xtb..." function within Avogadro after installing this extension

`xtb` and `crest` are distributed by the Grimme group under the LGPL license v3. The authors of Avogadro and avo_xtb bear no responsibility for xtb or crest or the contents of the Grimme group's repositories. Source code for the programs is available at the repositories linked above.

### Open Babel

The plugin also relies on Open Babel for conversion of output files to Avogadro's `cjson` format. The path to the `obabel` binary can be specified in the `Configure...` menu if it is not automatically detected. If you use Avogadro on Windows, macOS, or the AppImage or Flatpak on Linux, you have a recent build of `obabel` with CJSON support in the same folder as the Avogadro executable. If you have obtained it from a distro's repositories, your version of `obabel` ***does not*** have the necessary CJSON support, and you will unfortunately have to compile it yourself from the [latest code](https://github.com/openbabel/openbabel).

# Cite

For GFN2-xTB (default method):
* C. Bannwarth, S. Ehlert and S. Grimme., *J. Chem. Theory Comput.*, **2019**, 15, 1652-1671. DOI: [10.1021/acs.jctc.8b01176](https://dx.doi.org/10.1021/acs.jctc.8b01176)

For CREST (conformer searches):
* P. Pracht, F. Bohle, S. Grimme, *Phys. Chem. Chem. Phys.*, **2020**, 22, 7169-7192. DOI: [10.1039/C9CP06869D](https://dx.doi.org/10.1039/C9CP06869D)

See the xtb GitHub repository for other citations.
