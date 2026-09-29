#!/usr/bin/env python3
import glob
import hashlib
import os
import shutil
import subprocess

import jinja2

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
DEBIAN = os.path.join(REPO, "debian")
TEMPLATES = os.path.join(DEBIAN, "templates")
BUILD_ROOT = os.path.join(REPO, "build")
OUTDIR = os.path.join(BUILD_ROOT, "dist")
STAGING = os.path.join(BUILD_ROOT, "staging")
TITLES_DIR = "/var/lib/audiobible/titles"
VERSION = "1.0"
MAINTAINER = "Reuben Institute <reubeninstitute@gmail.com>"
PKG = "audiobible-titles"

JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(TEMPLATES),
    keep_trailing_newline=True,
)


def discover_files():
    files = sorted(
        os.path.basename(p)
        for p in glob.glob(os.path.join(REPO, "*.mp3")) + glob.glob(os.path.join(REPO, "*.csv"))
    )
    return files


def write_control(pkg_root, description):
    debian_dir = os.path.join(pkg_root, "DEBIAN")
    os.makedirs(debian_dir, exist_ok=True)
    os.chmod(debian_dir, 0o755)

    size_kb = sum(
        os.path.getsize(os.path.join(dirpath, f))
        for dirpath, _, files in os.walk(pkg_root)
        if "DEBIAN" not in dirpath.split(os.sep)
        for f in files
    ) // 1024

    rendered = JINJA_ENV.get_template("control.j2").render(
        pkg=PKG,
        version=VERSION,
        maintainer=MAINTAINER,
        size_kb=size_kb,
        description=description,
    )
    control = os.path.join(debian_dir, "control")
    with open(control, "w") as fh:
        fh.write(rendered)
    os.chmod(control, 0o644)
    return debian_dir


def embed_scripts(debian_dir):
    for name in ("bump-version.sh", "fast-build.sh"):
        src = os.path.join(DEBIAN, name)
        dst = os.path.join(debian_dir, name)
        shutil.copy(src, dst)
        os.chmod(dst, 0o755)


def write_md5sums(pkg_root):
    debian_dir = os.path.join(pkg_root, "DEBIAN")
    lines = []
    for dirpath, _, files in os.walk(pkg_root):
        if "DEBIAN" in dirpath.split(os.sep):
            continue
        for f in sorted(files):
            path = os.path.join(dirpath, f)
            rel = os.path.relpath(path, pkg_root)
            with open(path, "rb") as fh:
                digest = hashlib.md5(fh.read()).hexdigest()
            lines.append(f"{digest}  {rel}\n")
    md5sums = os.path.join(debian_dir, "md5sums")
    with open(md5sums, "w") as fh:
        fh.writelines(sorted(lines))
    os.chmod(md5sums, 0o644)


def build_deb(pkg_root):
    os.makedirs(OUTDIR, exist_ok=True)
    out = os.path.join(OUTDIR, f"{PKG}_{VERSION}_all.deb")
    env = dict(os.environ, TMPDIR=OUTDIR)
    subprocess.run(
        ["dpkg-deb", "-b", "-Zgzip", "-z1", pkg_root, out], check=True, env=env
    )
    shutil.rmtree(pkg_root)
    return out


def stage_files(pkg_root, filenames):
    titles_dir = pkg_root + TITLES_DIR
    os.makedirs(titles_dir, exist_ok=True)
    for path in [pkg_root, pkg_root + "/var", pkg_root + "/var/lib",
                 pkg_root + "/var/lib/audiobible", titles_dir]:
        os.chmod(path, 0o755)
    for name in filenames:
        dst = os.path.join(titles_dir, name)
        shutil.copy(os.path.join(REPO, name), dst)
        os.chmod(dst, 0o644)


def main():
    filenames = discover_files()
    if not filenames:
        raise SystemExit(f"No *.mp3/*.csv files found in {REPO} -- nothing to build.")

    pkg_root = os.path.join(STAGING, PKG)
    if os.path.exists(pkg_root):
        shutil.rmtree(pkg_root)

    stage_files(pkg_root, filenames)

    description = (
        "Parashah and psalm titles, DarkKnox2 voice\n"
        " Parashah and psalm titles in the DarkKnox2 voice."
    )
    debian_dir = write_control(pkg_root, description)
    embed_scripts(debian_dir)
    write_md5sums(pkg_root)
    out = build_deb(pkg_root)
    print(f"built {out}")


if __name__ == "__main__":
    main()
