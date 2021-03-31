import argparse
import difflib
import json
from pathlib import Path
from pprint import pformat
import sys


from esprr_api.main import app
from esprr_api.models import SURFACE_ALBEDOS


dashdir = Path(__file__).parent / "dashboard"
OPENAPI_PATH = dashdir / "tests/unit/openapi.json"
constdir = dashdir / "src/constants"
ALBEDO_PATH = constdir / "surface_albedo.json"


def printdiff(old, new):
    print(
        "\n".join(
            list(
                difflib.context_diff(
                    pformat(old, sort_dicts=False).split("\n"),
                    pformat(new, sort_dicts=False).split("\n"),
                    lineterm="",
                    fromfile="current",
                    tofile="latest",
                )
            )
        )
    )


def check_file(path, name, new):
    if not path.is_file():
        print(f"{name} does not exist")
        return 1
    else:
        old = json.loads(path.read_text())
        if old != new:
            print(f"{name} out of date")
            printdiff(old, new)
            return 1
    return 0


def write_json(path, new):
    with path.open("w") as f:
        json.dump(new, f, separators=(",", ":"))
        f.write("\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract API files for dashboard consumption"
    )
    parser.add_argument("--check", action="store_true", help="Check for file changes")
    args = parser.parse_args()

    new_openapi = app.openapi()
    new_openapi["info"]["version"] = "1"

    if args.check:
        ecode = sum(
            [
                check_file(OPENAPI_PATH, "OpenAPI spec", new_openapi),
                check_file(ALBEDO_PATH, "Surface albedo", SURFACE_ALBEDOS),
            ]
        )
        sys.exit(ecode)
    else:
        write_json(OPENAPI_PATH, new_openapi)
        write_json(ALBEDO_PATH, SURFACE_ALBEDOS)
