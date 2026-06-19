"""Package the project as a Kaggle-style submission tarball.

The Kaggle Agents runtime expects:
    /kaggle_simulations/agent/<our files>

We produce a tarball containing exactly the files the runtime needs:
``main.py``, ``deck.csv`` and the entire ``cg/`` SDK directory.

Usage:
    # Package the zoni agent (default)
    python scripts/package_submission.py --agent agents/zoni

    # Package zero_mexico
    python scripts/package_submission.py --agent agents/zero_mexico

    # Custom output
    python scripts/package_submission.py --agent agents/zoni --out artifacts/zoni_v2.tar.gz

CRITICAL: the cg/ submodule (containing the CABT native engine and Python
wrappers) MUST be included. Kaggle does NOT provide cg/ on the python path
automatically; without it, every agent() call fails with ImportError.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tarfile


_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def package(agent_dir: str, out_path: str) -> str:
    """Create the submission tarball. Returns the path written.

    Args:
        agent_dir: Path to the agent folder containing main.py and deck.csv
                   (e.g. "agents/zoni").
        out_path: Destination path for the .tar.gz file.
    """
    agent_full = os.path.join(_HERE, agent_dir) if not os.path.isabs(agent_dir) else agent_dir
    if not os.path.isdir(agent_full):
        raise FileNotFoundError(f"Agent directory not found: {agent_full}")
    main_src = os.path.join(agent_full, "main.py")
    deck_src = os.path.join(agent_full, "deck.csv")
    if not os.path.isfile(main_src):
        raise FileNotFoundError(f"main.py not found in {agent_full}")
    if not os.path.isfile(deck_src):
        raise FileNotFoundError(f"deck.csv not found in {agent_full}")

    # Use a clean staging dir to avoid leftover __pycache__ from previous runs
    staging = os.path.join(_HERE, "artifacts", "_submission_staging")
    if os.path.isdir(staging):
        shutil.rmtree(staging)
    os.makedirs(staging, exist_ok=True)

    # Copy main.py + deck.csv
    shutil.copy(main_src, os.path.join(staging, "main.py"))
    shutil.copy(deck_src, os.path.join(staging, "deck.csv"))

    # Copy cg/ SDK (the CABT engine). Skip __pycache__ to keep submission small.
    cg_src = os.path.join(_HERE, "cg")
    if not os.path.isdir(cg_src):
        raise FileNotFoundError(
            f"cg/ engine directory not found at {cg_src}. "
            "Download from Kaggle competition data: "
            "kaggle competitions download -c pokemon-tcg-ai-battle "
            "-f sample_submission/cg/api.py  (etc.)"
        )

    def _ignore(dirpath, names):
        return [n for n in names if n == "__pycache__"]

    shutil.copytree(cg_src, os.path.join(staging, "cg"), ignore=_ignore)

    # Make tarball. Order: main.py, deck.csv at root, then cg/ contents at cg/.
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    if os.path.exists(out_path):
        os.remove(out_path)
    with tarfile.open(out_path, "w:gz") as tf:
        # Root files first
        for name in ("main.py", "deck.csv"):
            fp = os.path.join(staging, name)
            if os.path.isfile(fp):
                tf.add(fp, arcname=name)
        # cg/ submodule second
        for name in sorted(os.listdir(os.path.join(staging, "cg"))):
            fp = os.path.join(staging, "cg", name)
            if os.path.isfile(fp):
                tf.add(fp, arcname=f"cg/{name}")

    # Verify
    size = os.path.getsize(out_path)
    print(f"Wrote {out_path} ({size/1024:.1f} KB)")
    with tarfile.open(out_path, "r:gz") as tf:
        names = sorted(tf.getnames())
    print("Contents:")
    for n in names:
        print(f"  {n}")
    return out_path


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    p.add_argument("--agent", default="agents/zoni", help="Agent directory containing main.py + deck.csv")
    p.add_argument("--out", default=None, help="Output tarball path (default: artifacts/<agent_name>.tar.gz)")
    args = p.parse_args()

    if args.out is None:
        agent_name = os.path.basename(args.agent.rstrip("/"))
        args.out = os.path.join(_HERE, "artifacts", f"{agent_name}.tar.gz")

    package(args.agent, args.out)


if __name__ == "__main__":
    main()
