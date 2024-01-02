#!/usr/bin/env python3

"""
This script updates paths in a structured config file, i.e. JSON or YAML.
"""

import argparse
import contextlib
import fileinput
import json
import pathlib

import jsonpath_ng
import ruamel.yaml


def infer_format(path: pathlib.Path):
    if path.suffix in {".yml", ".yaml"}:
        print(f"[INFO ]   inferred YAML format from extension")
        return "yaml"
    elif path.suffix == ".json":
        print(f"[INFO ]   inferred JSON format from extension")
        return "json"
    elif path.name == "Dockerfile":
        print(f"[INFO ]   inferred Dockerfile format from filename")
        return "dockerfile"
    else:
        print(f"[ERROR]   unable to infer format from filename - {path.name}")
        raise SystemExit(1)


@contextlib.contextmanager
def dockerfile_data(path: pathlib.Path):
    """
    For a Dockerfile, the 'data' is a dictionary of build ARGs.
    """
    data = {}

    print("[INFO ]   reading build args")
    with path.open() as fd:
        for line in fd.readlines():
            if not line.startswith("ARG "):
                continue
            parts = line.removeprefix("ARG ").strip().split("=", maxsplit = 1)
            try:
                name, value = parts
            except ValueError:
                name = parts[0]
                value = None
            data[name] = value

    yield data

    print("[INFO ]   writing updated build args")
    with fileinput.input(files = path, inplace = True) as fd:
        for line in fd:
            if not line.startswith("ARG "):
                print(line, end = "")
                continue
            name = line.removeprefix("ARG ").strip().split("=", maxsplit = 1)[0]
            value = data.get(name)
            if value is not None:
                print(f"ARG {name}={value}")
            else:
                print(f"ARG {name}")


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


CONFIG_DATA = { "dockerfile": dockerfile_data, "json": json_data, "yaml": yaml_data }


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
        choices = ["", "dockerfile", "json", "yaml"]
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
        path_format = infer_format(args.path)

    print(f"[INFO ] applying updates")
    with CONFIG_DATA[path_format](args.path) as data:
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
