"""
For now, all other scripts in the plugin import easyxtb via this module.

As such, this takes the role that __init__.py would normally and runs some code to make sure
everything is set up correctly.
"""

import sys

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
