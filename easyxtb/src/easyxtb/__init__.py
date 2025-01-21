import logging

from .configuration import config, save_config, reload_paths
from .configuration import PLUGIN_DIR, CALCS_DIR, TEMP_DIR, BIN_DIR
from .program import Program, XTB, CREST
from .geometry import Atom, Geometry
from .calc import Calculation
from . import calculate


logger = logging.getLogger(__name__)
logging.basicConfig(
    filename=PLUGIN_DIR / "log.log",
    filemode="w",
    format="%(name)s:%(lineno)s: %(message)s",
    encoding="utf-8",
    level=logging.DEBUG,
)
