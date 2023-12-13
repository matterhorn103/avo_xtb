"""
avo_xtb
A full-featured interface to xtb in Avogadro 2.
Copyright (c) 2023, Matthew J. Milner

BSD 3-Clause License

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import argparse
import json
import platform
import sys
import tarfile
import urllib.request
import zipfile

from pathlib import Path

from config import config, calc_dir, xtb_bin

# For now just hard code the URLs of xtb and crest
if platform.system() == "Windows":
    xtb_url = "https://github.com/grimme-lab/xtb/releases/download/v6.6.1/xtb-6.6.1-windows-x86_64.zip"
    crest_url = "Not available for Windows!"
elif platform.system() == "Darwin":
    xtb_url = "Not available for macOS!"
    crest_url = "Not available for macOS!"
elif platform.system() == "Linux":
    xtb_url = "https://github.com/grimme-lab/xtb/releases/download/v6.6.1/xtb-6.6.1-linux-x86_64.tar.xz"
    crest_url = "https://github.com/crest-lab/crest/releases/download/v2.12/crest.zip"


def download(url, parent_dir):
    archive_name = url.split("/")[-1]
    archive_path = parent_dir / archive_name
    urllib.request.urlretrieve(url, archive_path)
    return archive_path


def extract_zip(archive, target):
    with zipfile.ZipFile(archive, "r") as zip:
        zip.extractall(target)


def extract_tar(archive, target):
    with tarfile.open(archive, "r:xz") as tar:
        tar.extractall(target)


def get_xtb(url, install_dir):
    archive = download(url, install_dir)
    if archive.suffix == ".zip":
        extract_zip(archive, install_dir)
    else:
        extract_tar(archive, install_dir)
    xtb_folder = archive.with_name("-".join(archive.stem.split("-")[0:2]))
    # Rename unzipped folder to non-versioned so that config.py finds it
    xtb_folder.rename(xtb_folder.with_name("xtb"))
    # Remove archive
    archive.unlink()


def get_crest(url, install_dir):
    # Don't install crest if url not valid
    if url[0:5] != "https":
        return
    else:
        archive = download(url, install_dir)
        if archive.suffix == ".zip":
            extract_zip(archive, install_dir / "xtb" / "bin")
        else:
            extract_tar(archive, install_dir / "xtb" / "bin")
        # Remove archive
        archive.unlink()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--print-options", action="store_true")
    parser.add_argument("--run-command", action="store_true")
    parser.add_argument("--display-name", action="store_true")
    parser.add_argument("--lang", nargs="?", default="en")
    parser.add_argument("--menu-path", action="store_true")
    args = parser.parse_args()

    if args.print_options:
        options = {
            "userOptions": {
                "info": {
                    "type": "text",
                    "label": "Info",
                    "default": "xtb was not found on launch!\nThis tool can install it for you.",
                    "order": 1.0
                },
                "xtb_url": {
                    "type": "text",
                    "label": "xtb URL",
                    "default": xtb_url,
                    "order": 2.0
                },
                "crest_url": {
                    "type": "text",
                    "label": "crest URL",
                    "default": crest_url,
                    "order": 3.0
                },
                "install_dir": {
                    "type": "string",
                    "label": "Install in",
                    "default": str(calc_dir.parent),
                    "order": 5.0
                },
                "notice": {
                    "type": "text",
                    "label": "By clicking OK",
                    "default": "xtb and crest will be installed from the Grimme group repositories to the above location.",
                    "order": 6.0
                },
                "license": {
                    "type": "text",
                    "label": "Important",
                    "default": "xtb and crest are distributed independently under the LGPL license v3.\nThe authors of Avogadro and avo_xtb bear no responsibility for xtb or crest or the contents of the Grimme group's repositories.\nSource code for the programs is available at the above web addresses.",
                    "order": 7.0
                }
            }
        }
        print(json.dumps(options))
    if args.display_name:
        print("Get xtb…")
    if args.menu_path:
        # Only show menu option if xtb binary was not found
        if xtb_bin is None:
            print("Extensions|Semi-empirical (xtb){30}")
        else:
            pass

    if args.run_command:
        # Read input from Avogadro
        avo_input = json.loads(sys.stdin.read())

        install_dir = Path(avo_input["install_dir"])

        if platform.system() == "Darwin":
            result = {"message": "The Grimme group does not supply binaries for macOS.\nYou will have to install xtb manually.\nSorry!"}
        
        else:
            get_xtb(xtb_url, install_dir)
            get_crest(crest_url, install_dir)
            # Report success
            result = {"message": "xtb (and crest if requested) were successfully installed.\nPlease restart Avogadro."}
        
        # Pass back to Avogadro to display to user
        print(json.dumps(result))

