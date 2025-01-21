# Getting started

## Installation

### `easyxtb`

`easyxtb` is available from the [PyPI repository](https://pypi.org/project/easyxtb/) so it can be imported using any PyPI-compatible Python package manager.

With `pip`, for example, activate your [virtual environment](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/) and run:

```sh
$ pip install easyxtb
```

If you are using a Python project manager that supports [inline metadata](https://packaging.python.org/en/latest/specifications/inline-script-metadata/) such as [uv](https://docs.astral.sh/uv/), you can use it on a per-script basis without worrying about virtual environments by adding the following to the top of your script:

```python
# /// script
# dependencies = [
#   "easyxtb",
# ]
# ///
```

### xtb

You must obtain the `xtb` binary separately yourself; it is not bundled with the package.

An existing `xtb` binary will be picked up automatically by `easyxtb` if located in one of the following locations:
1. The system or user PATH
2. Within the `easyxtb` binary directory at `<user data>/easyxtb/bin/xtb` (see below for more information on where this is on your system)
3. Within the folder it is distributed in under the `easyxtb` binary directory, which would thus currently be at `<user data>/easyxtb/bin/xtb-dist/bin/xtb`
4. Any other location but with a link to it from `<user data>/easyxtb/bin/xtb`

Alternatively, the location of `xtb` can be specified from Python code simply by setting `easyxtb.XTB.path` to an appropriate `pathlib.Path` object.

The package has only been tested for `xtb >= 6.7`.

### CREST

`crest` can be made visible to the plugin in the same ways as for `xtb` listed above.
If it is not in `$PATH`, the `crest` binary, or a link to it, should be located at `<user data>/easyxtb/bin/crest`.
To specify the path to the variable from Python, set `easyxtb.CREST.path`.

Note that while `xtb` is cross-platform, `crest` is currently distributed only for Linux/UNIX systems.

The package has only been tested for `crest >= 3.0`.

## Import

`easyxtb` makes its key functionality accessible at the top level, so simply import it with:

```python
import easyxtb
```

## Handling molecular geometries

For more detailed information, see [Atoms & Geometries](geometry.md).

### Loading a geometry from file

To load a geometry (XYZ and CJSON files are supported currently):

```python
from pathlib import Path
import easyxtb

input_geom = easyxtb.Geometry.load_file(Path.home() / "calcs/benzoic_acid.xyz")
for atom in input_geom:
    print(atom)
# This prints:
Atom(element='C', x=-3.61652, y=0.64945, z=-0.0)
Atom(element='C', x=-3.59105, y=-1.15881, z=-0.0)
Atom(element='O', x=2.9034, y=0.39476, z=1e-05)
Atom(element='H', x=2.60455, y=-0.50701, z=2e-05)
# ...and so on
```

Charge and spin are picked up automatically from a CJSON file, but for XYZ files or for overriding the automatic detection they can be specified:

```python
acetate_anion = easyxtb.Geometry.from_file(Path.home() / "calcs/acetate.xyz", charge=-1)
```

Note that `easyxtb` follows the convention used by xtb itself, where `spin` is the number of unpaired electrons.

Methods are also provided to create geometries from an XYZ in the form of a `list` of lines, an XYZ containing multiple geometries, and from a CJSON in the form of a `dict`.

### Saving a geometry to file

This is easily done either a method specifically for XYZ or CJSON format, allowing for extra arguments:

```python
output_geom.write_xyz("./output.xyz", comment="Some very useful info to write on line 2")
output_geom.write_cjson("./output.cjson", indent=4)
```

or a convenient general method that picks the format based on the filename suffix but takes no further arguments:

```python
output_geom.write_file("./output.xyz")
```

## Running calculations

The package provides two APIs for running calculations: a [function-based API](calculate.md) that is simple to use and directly returns the key result of interest from a calculation, and a [calculation-based API](calculation.md) that provides greater control over the setup of the calculation and access to all of the output data.

### Using the function-based API with the `calculate` module

Functions are provided to directly obtain key results with xtb (`energy`, `optimize`, `frequencies`, `opt_freq`, `orbitals`) or CREST (`conformers`, `tautomerize`, `protonate`, `deprotonate`, `solvate`). These can be found within the `easyxtb.calculate` module.

For example, we can get an optimized geometry quickly with e.g.:

```python
from pathlib import Path
import easyxtb

input_geom = easyxtb.Geometry.from_file(Path.home() / "calcs/benzoic_acid.xyz")
optimized = easyxtb.calculate.optimize(input_geom, level="normal", solvation="water")
```

Then we can check if we found a minimum on the potential energy surface:

```python
freqs = easyxtb.calculate.frequencies(optimized, solvation="water")
print(freqs[0])
# Prints:
{'mode': 1, 'symmetry': 'a', 'frequency': -816.7902, 'reduced_mass': 12.1428, 'ir_intensity': 7.2604, 'raman_scattering_activity': 0.0, 'eigenvectors': [[-0.26, -0.46, 0.0], [-0.24, 0.43, -0.0], [-0.05, -0.05, 0.0], [0.08, 0.3, -0.0], [0.42, 0.02, -0.0], [-0.02, 0.03, -0.0], [0.24, -0.09, -0.0], [0.0, -0.02, 0.0], [-0.26, 0.1, 0.0], [0.05, 0.01, -0.0], [-0.02, -0.03, 0.0], [0.0, -0.21, 0.0], [0.05, 0.0, -0.0], [-0.02, 0.01, -0.0]]}
```

We were returned at least one negative frequency!

The xtb team recommend generally using the `ohess` (optimization followed by a frequency calculation) runtype as, in the case of negative frequencies, xtb will produce a distorted geometry along the imaginary mode.
The `opt_freq()` calculation function takes advantage of this and will continue reoptimizing using these distorted geometries until a minimum is reached, so is more reliable in getting what we want:

```python
output_geom, output_freqs = easyxtb.calculate.opt_freq(input_geom, level="normal", solvation="water")
print(output_freqs[0])
# Prints:
{'mode': 1, 'symmetry': 'a', 'frequency': 70.0622, 'reduced_mass': 13.4154, 'ir_intensity': 6.422, 'raman_scattering_activity': 0.0, 'eigenvectors': [[0.0, 0.0, -0.28], [-0.0, 0.0, -0.0], [-0.0, -0.0, 0.25], [0.0, -0.0, 0.04], [0.0, -0.0, -0.24], [-0.0, 0.0, -0.0], [-0.0, 0.0, 0.29], [-0.0, 0.0, 0.15], [0.0, -0.0, 0.02], [0.0, -0.0, -0.12], [0.0, 0.0, -0.15], [0.0, -0.0, 0.55], [0.0, 0.01, -0.56], [0.0, 0.0, -0.19]]}
```

Each function takes extra arguments to specify common xtb/CREST options.
The default value for these arguments is usually `None`, but if they are left as `None` the values are generally taken from the user config.

For further details on the available functions and the arguments they take see [the relevant page](calculate.md).

### Using the calculation-based API with the `Calculation` class

Sometimes you might want to adjust some aspects of the calculation before it is run, or you might need to access more of the output than is returned by a function in the `calculate` module.
For this we can create and manage a `Calculation` instance.

#### Runtype constructors

For convenience, the `Calculation` class has a number of class methods that serve as constructors for the same common runtypes as the function-based API provides.
These return a `Calculation` object, having taken care of most of the setup for you.

Each constructor also takes extra arguments as well to make it easier to specify common xtb/CREST options.
These arguments are named similarly to those of the functions in the `calculate` module.

To create a `Calculation` that is set up to run a geometry optimization with xtb, for example:

```python
calc = easyxtb.Calculation.opt(input_geom, level="normal")
print(calc.preview_command())
# Prints e.g.
[PosixPath('/home/user/.local/share/easyxtb/bin/xtb-dist/bin/xtb'), '--gfn', 2, '-p', 2, '--opt', 'normal', '--', <easyxtb.geometry.Geometry object at 0x7fd60b131820>]
```

The names of these constructor methods are generally those of the corresponding xtb or CREST runtype.
Note that this means they differ from the names of the functions in the `calculate` module.

For further details on the available constructors and the arguments they take see [the relevant page](calculation.md).

#### Custom `Calculation` instances

Sometimes you will need to create a `Calculation` from scratch.
You might want to use a runtype that doesn't yet have a corresponding function or constructor, for instance.

For example, to instantiate a `Calculation` similar to that returned by the `Calculation.opt()` constructor:

```python
from pathlib import Path
import easyxtb

input_geom = easyxtb.Geometry.from_file(Path.home() / "calcs/benzoic_acid.xyz")
calc = easyxtb.Calculation(
    program=easyxtb.XTB,
    input_geometry=input_geom,
    runtype="opt",
    runtype_args=["tight"], # Argument that should follow --opt
    options={
        "gfn": 2,           # GFN-xTB parameterization
        "alpb": "water",    # Solvation
        "p": 4,             # Number of threads
    },
)
```

The first argument of `Calculation.__init__()` takes an instance of the [`Program`](program.md) class.
You will pretty much always want to pass either `easyxtb.XTB` and `easyxtb.CREST` for this – instances of `Program` set up at import time with the right paths to the binaries.

### Running a `Calculation` and accessing the results

Once a `Calculation` is set up to your liking, start it using:

```python
calc = easyxtb.Calculation.opt(input_geom, level="normal")
calc.run()
```

The details of starting the respective program on the command line and where to store the input and output files will then be taken care for you automatically.
The thread will remain busy until the calculation has run its course and the program has exited.

Once the calculation has finished, the output files produced will be automatically detected and processed and the results stored as attributes of the `Calculation` instance as native Python objects.

For example, after running our optimization we can get the optimized geometry easily:

```python
calc = easyxtb.Calculation.opt(input_geom, level="normal")
calc.run()
output_geom = calc.output_geometry  # A normal `Geometry` object
print(calc.output_geometry.atoms)
# Prints:
Atom(element='C', x=-2.94841377173243, y=0.53595421697827, z=-0.00205114575446)
Atom(element='C', x=-2.96353116164446, y=-0.85021326429608, z=-0.00028605784754)
# ...and so on
```

Note that attributes are only valid when result data have been found for them and attempting to access them otherwise (trying to access `Calculation.frequencies` after running an optimization, for example) will raise an `AttributeError`.

See the documentation page for [`Calculation`](calculation.md) for details on the attributes under which result data are made available.

## Configuration

The user configuration is stored at `PLUGIN_DIR/config.json` (see below for where this can be found) and can be manually changed in a text editor.

A better way to view and handle configuration from Python is planned but for now the user configuration is stored in a simple `dict` that can be manipulated as normal:

```python
print(easyxtb.config["opt_lvl"])
# Prints 'normal' if left at the default value
easyxtb.config["opt_lvl"] = "vtight"
print(easyxtb.config["opt_lvl"])
# Prints 'vtight'
```

Changes to non-path variables in your configuration will affect future uses of the functions in the `calculate` module and the options used for `Calculation` instances created with the runtype constructors.
Existing `Calculation` instances will be unaffected.

The changes will not be persistent beyond the current Python interpreter/process unless you save your configuration:

```python
easyxtb.config["opt_lvl"] = "vtight"
```

Changes to path variables via your configuration will have no immediate effect and will only have an effect if you manually reload the paths:

```python
print(easyxtb.CALCS_DIR)
# PosixPath('/home/user/.local/share/easyxtb')
easyxtb.config["calcs_dir"] = "/home/user/calcs/xtb"
easyxtb.reload_paths()
print(easyxtb.CALCS_DIR)
# PosixPath('/home/user/calcs/xtb')
```

## Data location (`PLUGIN_DIR`)

`easyxtb` uses a central location to run its calculations, store its configuration, and save its log file.
This location is `<user data>/easyxtb`, where `<user data>` is OS-dependent:

- Windows: `$USER_HOME\AppData\Local\easyxtb`
- macOS: `~/Library/Application Support/easyxtb`
- Linux: `~/.local/share/easyxtb`

Additionally, if the environment variable `XDG_DATA_HOME` is set its value will be respected and takes precedence over the above paths (on all OSes).

The constant `easyxtb.PLUGIN_DIR` is set to the data location.
