Welcome to the documentation for the `easyxtb` Python package.

## Introduction

`easyxtb` is an unofficial API for the xtb and CREST semi-empirical quantum chemistry programs with an emphasis on intuitive and straightforward usage.

It forms the basis for [`avo_xtb`](https://github.com/matterhorn103/avo_xtb), a plugin for the 3D chemical visualization software [Avogadro 2](https://two.avogadro.cc) that provides an in-app interface to the xtb program for quick and accurate calculations, as well as the CREST program for extended functionality.

The Python package `easyxtb` can be used independently of `avo_xtb` as an interface to launch calculations and process their results from Python.

[`xtb`](https://github.com/grimme-lab/xtb) is developed by the Grimme group in Bonn and carries out semi-empirical quantum mechanical calculations using the group's e**x**tended **T**ight-**B**inding methods, referred to as "GFNn-xTB".

These methods provide fast and reasonably accurate calculation of **G**eometries, **F**requencies, and **N**on-covalent interactions for molecular systems with up to roughly 1000 atoms, with broad coverage of the periodic table up to *Z* = 86 (radon).

[`crest`](https://github.com/crest-lab/crest) (Conformer–Rotamer Ensemble Sampling Tool) adds a variety of sampling procedures for several interesting applications including conformer searches, thermochemistry, and solvation.

## Usage

For an overview on how to use the package, see [Getting started](guide.md).

The remaining pages in the documentation cover the user-facing parts of the Python API in more detail.

## Further reading

For more detail on the meaning of each program's runtypes and command line options, see their documentation:

- [`xtb`](https://xtb-docs.readthedocs.io/en/latest/index.html)
- [`crest`](https://crest-lab.github.io/crest-docs/)
