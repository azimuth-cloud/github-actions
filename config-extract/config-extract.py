#!/usr/bin/env python3

"""
This script extracts values from a structured config file, i.e. JSON or YAML.
"""

import argparse
import contextlib
import json
import os
import pathlib

import jsonpath_ng
import yaml


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


@contextlib.contextmanager
def json_data(path: pathlib.Path):
    print("[INFO ]   reading data")
    with path.open() as fd:
        yield json.load(fd)


@contextlib.contextmanager
def yaml_data(path: pathlib.Path):
    print("[INFO ]   reading data")
    with path.open() as fd:
        yield yaml.safe_load(fd)


CONFIG_DATA = { "dockerfile": dockerfile_data, "json": json_data, "yaml": yaml_data }


def produce_output(name, value):
    output_path = os.environ.get("GITHUB_OUTPUT", "/dev/stdout")
    with open(output_path, "a") as fd:
        print(f"{name}={value}", file = fd)


def main():
    parser = argparse.ArgumentParser(description = "Extracts values from a structured config file.")
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
        "outputs",
        help = "The set of outputs to produce, one per line in the format 'name=json-path-expr'."
    )
    args = parser.parse_args()

    print(f"[INFO ] extracting from config file {args.path}")

    if args.format:
        print(f"[INFO ]   using specified format - {args.format}")
        path_format = args.format
    else:
        path_format = infer_format(args.path)

    print(f"[INFO ] extracting values")
    with CONFIG_DATA[path_format](args.path) as data:
        for output in args.outputs.splitlines():
            # Ignore empty lines
            if not output:
                continue
            name, jsonpath = output.split("=", maxsplit = 1)
            print(f"[INFO ]   extracting {jsonpath} as {name}")
            jsonpath_expr = jsonpath_ng.parse(jsonpath)
            try:
                value = next(
                    match.value
                    for match in jsonpath_expr.find(data)
                )
            except StopIteration:
                print(f"[WARN ]   no value at {jsonpath}")
            else:
                produce_output(name, value)


if __name__ == "__main__":
    main()
