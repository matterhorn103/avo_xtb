import logging

from .configuration import config, config_file
from .configuration import PLUGIN_DIR, CALC_DIR, TEMP_DIR, BIN_DIR, XTB_BIN, CREST_BIN
from .geometry import Atom, Geometry
from .calculate import Calculation
from . import calculate, configuration, convert, format


logger = logging.getLogger(__name__)
logging.basicConfig(
    filename=PLUGIN_DIR / "log.log",
    filemode="w",
    format="%(name)s:%(lineno)s: %(message)s",
    encoding="utf-8",
    level=logging.DEBUG,
)
