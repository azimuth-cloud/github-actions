#!/usr/bin/env python3

"""
This script updates paths in a structured config file, i.e. JSON or YAML.
"""

import argparse
import contextlib
import json
import pathlib

import jsonpath_ng
import ruamel.yaml


def format_from_extension(path: pathlib.Path):
    if path.suffix in {".yml", ".yaml"}:
        print(f"[INFO ]   inferred YAML format from extension")
        return "yaml"
    elif path.suffix == ".json":
        print(f"[INFO ]   inferred JSON format from extension")
        return "json"
    else:
        print(f"[ERROR]   unable to infer format from extension - {path.suffix}")
        raise SystemExit(1)


@contextlib.contextmanager
def json_data(path: pathlib.Path):
    print("[INFO ]   reading current data")
    with path.open() as fd:
        data = json.load(fd)

    yield data

    print("[INFO ]   writing updated data")
    with path.open("w") as fd:
        json.dump(data, fd, indent = 4)


@contextlib.contextmanager
def yaml_data(path: pathlib.Path):
    yaml = ruamel.yaml.YAML(typ = "rt")
    yaml.explicit_start = True
    yaml.preserve_quotes = True
    yaml.width = 1000000
    yaml.mapping_indent = 2
    yaml.sequence_indent = 4
    yaml.sequence_dash_offset = 2

    print("[INFO ]   reading current data")
    with path.open() as fd:
        data = yaml.load(fd)

    yield data

    print("[INFO ]   writing updated data")
    with path.open("w") as fd:
        yaml.dump(data, fd)


def main():
    parser = argparse.ArgumentParser(description = "Updates paths in a structured config file.")
    parser.add_argument(
        "path",
        help = "The path to the file to update.",
        type = pathlib.Path
    )
    parser.add_argument(
        "format",
        help = "The format of the file. If empty, the format is inferred from the path.",
        choices = ["", "json", "yaml"]
    )
    parser.add_argument(
        "updates",
        help = "The set of updates to apply, one per line in the format 'json-path-expr=value'."
    )
    args = parser.parse_args()

    print(f"[INFO ] updating config file {args.path}")

    if args.format:
        print(f"[INFO ]   using specified format - {args.format}")
        path_format = args.format
    else:
        path_format = format_from_extension(args.path)

    # Decide which context manager to use
    config_data = json_data if path_format == "json" else yaml_data

    print(f"[INFO ] applying updates")
    with config_data(args.path) as data:
        for update in args.updates.splitlines():
            # Ignore empty lines
            if not update:
                continue
            json_path, value = update.split("=", maxsplit = 1)
            print(f"[INFO ]   updating {json_path} to {value}")
            json_path_expr = jsonpath_ng.parse(json_path)
            json_path_expr.update(data, value)


if __name__ == "__main__":
    main()
