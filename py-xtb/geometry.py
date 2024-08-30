import json
from pathlib import Path

class Geometry:
    def __init__(self, atoms):
        self.atoms = atoms

    @classmethod
    def from_cjson(cls, cjson_dict: dict):
        return Geometry()

    @classmethod
    def from_xyz(cls, xyz_lines: list):
        return Geometry()

    @classmethod
    def from_file(cls, file, format=None):
        filepath = Path(file)
        # Autodetect format of file
        if format is None:
            format = filepath.suffix
        if format == ".xyz":
            with open(filepath, encoding="utf-8") as f:
                file_lines = f.read().split("\n")
            return cls.from_xyz(file_lines)
        if format == ".cjson":
            with open(filepath, encoding="utf-8") as f:
                cjson = json.load(f)
            return cls.from_cjson(cjson)
