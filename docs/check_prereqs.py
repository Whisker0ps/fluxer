#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Fluxer self-hosting prereq checker for Rocky/RHEL-like systems.

- Uses rpm/dnf + command probes to report presence and versions.
- Output is human readable and suitable for sharing back to the docs process.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Iterable, Optional, Tuple


@dataclass
class CheckResult:
	name: str
	status: str
	version: str
	details: str


@dataclass
class Requirement:
	name: str
	rpm_names: Tuple[str, ...] = ()
	commands: Tuple[str, ...] = ()
	min_version: Optional[str] = None
	version_cmd: Optional[Tuple[str, ...]] = None
	version_regex: Optional[str] = None


def run(cmd: Iterable[str]) -> Tuple[int, str, str]:
	try:
		proc = subprocess.run(
			list(cmd),
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			text=True,
		)
		return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
	except FileNotFoundError as exc:
		return 127, "", f"{exc}"


def rpm_query(pkg: str) -> Optional[str]:
	code, out, _ = run(["rpm", "-q", "--qf", "%{VERSION}-%{RELEASE}", pkg])
	if code != 0:
		return None
	return out or None


def command_version(cmd: Tuple[str, ...], regex: str) -> Optional[str]:
	code, out, err = run(cmd)
	text = out or err
	if code != 0:
		return None
	match = re.search(regex, text)
	if not match:
		return None
	return match.group(1)


def parse_version_tuple(version: str) -> Tuple[int, ...]:
	parts = re.split(r"[^0-9]+", version)
	nums = [int(p) for p in parts if p.isdigit()]
	return tuple(nums) if nums else (0,)


def version_meets(version: str, minimum: str) -> bool:
	return parse_version_tuple(version) >= parse_version_tuple(minimum)


def check_requirement(req: Requirement) -> CheckResult:
	found_rpm = None
	for pkg in req.rpm_names:
		ver = rpm_query(pkg)
		if ver:
			found_rpm = f"{pkg} {ver}"
			break

	found_cmd = None
	for cmd in req.commands:
		if shutil.which(cmd):
			found_cmd = cmd
			break

	version = "-"
	if req.version_cmd and req.version_regex and found_cmd:
		v = command_version(req.version_cmd, req.version_regex)
		if v:
			version = v

	status = "missing"
	details = ""
	if found_rpm or found_cmd:
		status = "present"
		parts = []
		if found_rpm:
			parts.append(found_rpm)
		if found_cmd:
			parts.append(f"cmd:{found_cmd}")
		details = ", ".join(parts)

	if req.min_version and version != "-":
		if version_meets(version, req.min_version):
			status = "ok"
		else:
			status = "too-old"

	return CheckResult(req.name, status, version, details)


def print_table(results: Iterable[CheckResult]) -> None:
	headers = ("Name", "Status", "Version", "Details")
	rows = [headers]
	for r in results:
		rows.append((r.name, r.status, r.version, r.details))
	widths = [max(len(str(row[i])) for row in rows) for i in range(4)]

	def fmt(row: Tuple[str, str, str, str]) -> str:
		return "  ".join(str(row[i]).ljust(widths[i]) for i in range(4))

	print(fmt(headers))
	print("  ".join("-" * w for w in widths))
	for r in results:
		print(fmt((r.name, r.status, r.version, r.details)))


def main() -> int:
	parser = argparse.ArgumentParser(description="Fluxer prereq checker (Rocky/RHEL)")
	parser.add_argument("--json", action="store_true", help="Output JSON instead of a table")
	parser.add_argument(
		"--mode",
		choices=("container", "build", "all"),
		default="container",
		help="Check container-only runtime (default), host build toolchain, or all",
	)
	args = parser.parse_args()

	is_root = False
	try:
		is_root = (os.geteuid() == 0)
	except AttributeError:
		is_root = False

	container_requirements = [
		Requirement("podman", ("podman",), ("podman",), None, ("podman", "--version"), r"podman\s+([0-9.]+)"),
		Requirement("podman-compose", ("podman-compose",), ("podman-compose",), None, ("podman-compose", "--version"), r"([0-9.]+)"),
		Requirement("httpd", ("httpd",), ("httpd",), None, ("httpd", "-v"), r"Apache/([0-9.]+)"),
		Requirement("mod_ssl", ("mod_ssl",), (), None, None, None),
		Requirement("mod_md", ("mod_md",), (), None, None, None),
		Requirement("git", ("git",), ("git",), None, ("git", "--version"), r"([0-9.]+)"),
		Requirement("curl", ("curl",), ("curl",), None, ("curl", "--version"), r"curl\s+([0-9.]+)"),
	]

	build_requirements = [
		Requirement("node", ("nodejs",), ("node",), "24.0.0", ("node", "--version"), r"v([0-9.]+)"),
		Requirement("pnpm", (), ("pnpm",), "10.29.3", ("pnpm", "--version"), r"([0-9.]+)"),
		Requirement("erlang", ("erlang",), ("erl",), "28.0.0", ("erl", "-version"), r"([0-9.]+)"),
		Requirement("rebar3", (), ("rebar3",), "3.24.0", ("rebar3", "--version"), r"rebar3\s+([0-9.]+)"),
		Requirement("rustc", ("rust",), ("rustc",), "1.93.0", ("rustc", "--version"), r"rustc\s+([0-9.]+)"),
		Requirement("cargo", ("cargo",), ("cargo",), None, ("cargo", "--version"), r"cargo\s+([0-9.]+)"),
		Requirement("gcc", ("gcc",), ("gcc",), None, ("gcc", "--version"), r"gcc\s+\(GCC\)\s+([0-9.]+)"),
		Requirement("g++", ("gcc-c++",), ("g++",), None, ("g++", "--version"), r"\(GCC\)\s+([0-9.]+)"),
		Requirement("make", ("make",), ("make",), None, ("make", "--version"), r"GNU Make\s+([0-9.]+)"),
		Requirement("python3", ("python3",), ("python3",), None, ("python3", "--version"), r"Python\s+([0-9.]+)"),
		Requirement("openssl", ("openssl", "openssl-devel"), ("openssl",), None, ("openssl", "version"), r"OpenSSL\s+([0-9.]+)"),
		Requirement("sqlite", ("sqlite", "sqlite-libs", "sqlite-devel"), ("sqlite3",), None, ("sqlite3", "--version"), r"([0-9.]+)"),
		Requirement("libvips", ("vips", "libvips"), ("vips",), None, ("vips", "--version"), r"vips\s+([0-9.]+)"),
		Requirement("exiftool", ("perl-Image-ExifTool",), ("exiftool",), None, ("exiftool", "-ver"), r"([0-9.]+)"),
		Requirement("ffmpeg", ("ffmpeg",), ("ffmpeg",), None, ("ffmpeg", "-version"), r"ffmpeg\s+version\s+([0-9.]+)"),
		Requirement("libsqlite3-dev", ("sqlite-devel",), (), None, None, None),
		Requirement("libssl-dev", ("openssl-devel",), (), None, None, None),
	]

	if args.mode == "container":
		requirements = container_requirements
	elif args.mode == "build":
		requirements = build_requirements
	else:
		requirements = container_requirements + build_requirements

	results = [check_requirement(r) for r in requirements]

	if args.json:
		payload = {
			"root": is_root,
			"mode": args.mode,
			"results": [r.__dict__ for r in results],
		}
		print(json.dumps(payload, indent=2))
	else:
		print(f"Running as root: {'yes' if is_root else 'no'}")
		print(f"Mode: {args.mode}")
		print_table(results)

	missing = [r for r in results if r.status == "missing"]
	too_old = [r for r in results if r.status == "too-old"]
	if missing or too_old:
		print("\nSummary:")
		if missing:
			print(f"- Missing: {', '.join(r.name for r in missing)}")
		if too_old:
			print(f"- Too old: {', '.join(f'{r.name}<{r.version}' for r in too_old)}")

	return 1 if missing or too_old else 0


if __name__ == "__main__":
	sys.exit(main())
