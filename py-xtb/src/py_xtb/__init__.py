import logging

from .conf import config, config_file
from .conf import PLUGIN_DIR, CALC_DIR, TEMP_DIR, BIN_DIR, XTB_BIN, CREST_BIN
from .geometry import Atom, Geometry
from .calc import Calculation
from . import calc, conf, convert


logger = logging.getLogger(__name__)
logging.basicConfig(
    filename=PLUGIN_DIR / "log.log",
    filemode="w",
    format="%(name)s:%(lineno)s: %(message)s",
    encoding="utf-8",
    level=logging.DEBUG,
)
