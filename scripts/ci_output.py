#!/usr/bin/env python3
"""Shared GitHub Actions annotations and output-file helpers."""

from __future__ import annotations

import os
import re
import sys
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import TextIO


OUTPUT_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")


def _escape_data(value: str) -> str:
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _escape_property(value: str) -> str:
    return _escape_data(value).replace(":", "%3A").replace(",", "%2C")


def emit_error(
    message: str,
    *,
    title: str | None = None,
    file: str | None = None,
    stream: TextIO | None = None,
) -> None:
    destination = stream or sys.stdout
    print(f"error: {message}", file=destination)
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return

    properties = []
    if title:
        properties.append(f"title={_escape_property(title)}")
    if file:
        properties.append(f"file={_escape_property(file)}")
    suffix = f" {','.join(properties)}" if properties else ""
    print(f"::error{suffix}::{_escape_data(message)}", file=destination)


def write_github_outputs(path: Path | None, values: Mapping[str, object]) -> None:
    if path is None:
        return

    with path.open("a", encoding="utf-8") as output:
        for key, raw_value in values.items():
            if not OUTPUT_NAME.fullmatch(key):
                raise ValueError(f"invalid GitHub output name: {key}")
            value = str(raw_value)
            delimiter = f"ghadelimiter_{uuid.uuid4().hex}"
            while delimiter in value:
                delimiter = f"ghadelimiter_{uuid.uuid4().hex}"
            output.write(f"{key}<<{delimiter}\n{value}\n{delimiter}\n")
