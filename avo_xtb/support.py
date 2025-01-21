import sys

# Manipulate the Python Path to get everything we need from the easyxtb module
#sys.path.insert(0, str(Path(__file__).parent.parent / "easyxtb/src"))

# Make easyxtb available as to anything that imports support.py as if it was installed
import easyxtb


# Make sure stdout stream is always Unicode, as Avogadro 1.99 expects
sys.stdout.reconfigure(encoding="utf-8")


# Piggyback the easyxtb config and add some extra plugin-specific things
plugin_defaults = {
    "energy_units": "kJ/mol",
    "xtb_opts": {},
    "crest_opts": {},
}
for k, v in plugin_defaults.items():
    if k not in easyxtb.config:
        easyxtb.config[k] = v
