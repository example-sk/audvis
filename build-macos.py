#!/usr/bin/env python3
"""Build self-contained Blender extension ZIPs for Apple silicon and Intel Macs."""
import argparse
import ast
from pathlib import Path
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent
TARGETS = {
    "macos-arm64": "macosx_11_0_arm64",
    "macos-x64": "macosx_12_0_x86_64",
}


def build(target, download=True, blender_version="4.2"):
    modern = blender_version == "5.2"
    if modern and target != "macos-arm64":
        raise ValueError("Official Blender 5.2 macOS builds support Apple silicon only")
    python_version = "3.13" if modern else "3.11"
    wheel_dir = ROOT / "wheels" / ("blender52" if modern else "") / target
    wheel_dir.mkdir(parents=True, exist_ok=True)
    if download:
        for requirements, extra in [
            ("requirements-blender52.txt" if modern else "requirements.txt", ["--no-deps"] if modern else []),
            ("requirements-blender52-nodeps.txt" if modern else "requirements-nodeps.txt", ["--no-deps"])]:
            subprocess.run([
                sys.executable, "-m", "pip", "download",
                "--disable-pip-version-check", "--only-binary=:all:",
                "--python-version", python_version, "--implementation", "cp",
                "--abi", "cp" + python_version.replace(".", ""), "--platform", TARGETS[target],
                "--dest", str(wheel_dir), "-r", str(ROOT / requirements),
                *extra,
            ], check=True)
    # Ignore stale downloads and Blender's own NumPy. Each package must have
    # exactly one version so extension wheel installation is unambiguous.
    requirement_files = (["requirements-blender52.txt", "requirements-blender52-nodeps.txt"]
                         if modern else ["requirements.txt", "requirements-nodeps.txt"])
    pins = {}
    for name in requirement_files:
        for line in (ROOT / name).read_text().splitlines():
            if line and not line.startswith("#"):
                package, version = line.split("==")
                pins[package.replace("-", "_")] = version
    pins["packaging"] = "23.2"
    wheels = sorted(wheel for wheel in wheel_dir.glob("*.whl")
                    if pins.get(wheel.name.split("-")[0]) == wheel.name.split("-")[1])
    for package in pins:
        matches = [wheel for wheel in wheels if wheel.name.split("-")[0] == package]
        if len(matches) != 1:
            raise RuntimeError("Expected one pinned wheel for " + package + ", found " + str(len(matches)))
    required = {"cffi", "pycparser", "pygame", "sounddevice", "soundfile",
                "mido", "packaging", "opencv_python"}
    missing = required - {wheel.name.split("-")[0] for wheel in wheels}
    if missing:
        raise RuntimeError("Missing wheels: " + ", ".join(sorted(missing)))
    for wheel in wheels:
        with zipfile.ZipFile(wheel) as archive:
            if archive.testzip():
                raise RuntimeError("Corrupt wheel: " + wheel.name)

    manifest = (ROOT / "blender_manifest.toml").read_text()
    version = re.search(r'^version = "([^"]+)"', manifest, re.M).group(1)
    if modern:
        manifest = re.sub(r'^blender_version_min = .*$', 'blender_version_min = "5.2.0"', manifest, flags=re.M)
    else:
        manifest = manifest.replace('blender_version_min = "4.2.0"',
                                    'blender_version_min = "4.2.0"\nblender_version_max = "5.1.0"')
    manifest = re.sub(r'^platforms = .*$', 'platforms = ["' + target + '"]',
                      manifest, flags=re.M)
    wheel_list = "wheels = [\n" + "".join(
        '    "./wheels/' + wheel.name + '",\n' for wheel in wheels) + "]"
    manifest = re.sub(r'^wheels = \[.*?\]', lambda _: wheel_list, manifest,
                      flags=re.M | re.S)
    output = ROOT / "dist" / ("audvis-" + version + ("-blender5.2" if modern else "") + "-" + target + ".zip")
    output.parent.mkdir(exist_ok=True)
    sources = sorted(ROOT.glob("*.py"))
    sources = [source for source in sources if source.name != Path(__file__).name]
    for directory in ["analyzer", "bge", "ui"]:
        sources.extend(sorted((ROOT / directory).rglob("*.py")))
    for source in sources:
        ast.parse(source.read_text(), filename=str(source))
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("blender_manifest.toml", manifest)
        for source in sources:
            archive.write(source, source.relative_to(ROOT).as_posix())
        for name in ["LICENSE", "README.md", "requirements.txt", "requirements-nodeps.txt"]:
            archive.write(ROOT / name, name)
        for source in ROOT.glob("requirements-blender52*.txt"):
            archive.write(source, source.name)
        for directory in ["analyzer", "bge", "ui"]:
            for source in sorted((ROOT / directory).rglob("*")):
                if source.is_file() and source.suffix != ".py" and "__pycache__" not in source.parts:
                    archive.write(source, source.relative_to(ROOT).as_posix())
        for source in sorted((ROOT / "doc").rglob("*")):
            if source.is_file():
                archive.write(source, source.relative_to(ROOT).as_posix())
        for wheel in wheels:
            archive.write(wheel, "wheels/" + wheel.name)
    with zipfile.ZipFile(output) as archive:
        if archive.testzip():
            raise RuntimeError("Archive integrity check failed")
    print("Built and verified: " + str(output))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", choices=["all", *TARGETS], default="all")
    parser.add_argument("--blender-version", choices=["4.2", "5.2"], default="4.2")
    parser.add_argument("--skip-download", action="store_true",
                        help="Use dependencies already downloaded into wheels/<platform>")
    args = parser.parse_args()
    targets = (["macos-arm64"] if args.blender_version == "5.2" else TARGETS) if args.platform == "all" else [args.platform]
    for target in targets:
        build(target, download=not args.skip_download, blender_version=args.blender_version)
