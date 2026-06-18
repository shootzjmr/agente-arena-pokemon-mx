"""Package the project as a Kaggle-style submission tarball.

The Kaggle Agents runtime expects:
    /kaggle_simulations/agent/<our files>

We produce ``artifacts/submission.tar.gz`` containing exactly the files the
runtime needs: ``main.py``, ``deck.csv`` and the entire ``cg/`` SDK directory.

Usage:
    python tools/package_submission.py [--deck PATH] [--out PATH] [--name LABEL]
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tarfile

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _HERE)


def package(deck_path: str, out_path: str) -> str:
    """Create the submission tarball. Returns the path written."""
    staging = os.path.join(_HERE, "artifacts", "_submission_staging")
    if os.path.isdir(staging):
        shutil.rmtree(staging)
    os.makedirs(staging, exist_ok=True)

    # Copy main.py
    shutil.copy(os.path.join(_HERE, "main.py"), os.path.join(staging, "main.py"))

    # Copy deck.csv
    if not os.path.isfile(deck_path):
        raise FileNotFoundError(deck_path)
    shutil.copy(deck_path, os.path.join(staging, "deck.csv"))

    # Copy cg/ SDK (skip __pycache__ to keep submission small)
    def _ignore(dirpath, names):
        return [n for n in names if n == "__pycache__"]
    shutil.copytree(os.path.join(_HERE, "cg"), os.path.join(staging, "cg"), ignore=_ignore)

    # Make tarball
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with tarfile.open(out_path, "w:gz") as tf:
        for name in os.listdir(staging):
            tf.add(os.path.join(staging, name), arcname=name)

    # Verify
    size = os.path.getsize(out_path)
    print(f"Wrote {out_path} ({size/1024:.1f} KB)")
    with tarfile.open(out_path, "r:gz") as tf:
        names = sorted(tf.getnames())
    print("Contents:")
    for n in names[:30]:
        print(f"  {n}")
    if len(names) > 30:
        print(f"  ... +{len(names) - 30} more files")
    return out_path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--deck", default=os.path.join(_HERE, "simple_deck.csv"))
    p.add_argument("--out", default=os.path.join(_HERE, "artifacts", "submission.tar.gz"))
    args = p.parse_args()
    package(args.deck, args.out)


if __name__ == "__main__":
    main()
