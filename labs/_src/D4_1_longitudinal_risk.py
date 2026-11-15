# /// script
# requires-python = ">=3.12"
# dependencies = ["polars>=2.0", "pyyaml>=6.0", "psutil>=7.0"]
# ///
# %% [markdown]
# # Lab 4.1 · Sequences as quasi-identifiers
#
# Day 4 · Session 1 (Disclosure risk in longitudinal records) · 25 min.
#
# Measure re-identification risk when encounter sequences act as quasi-identifiers and compare it with the single-table estimate, then coarsen and measure again.
#
# **Tasks**
# - [ ] 1 · The single-table estimate (5')
# - [ ] 2 · Sequences an adversary could know (7')
# - [ ] 3 · Risk by number of known encounters (5')
# - [ ] 4 · Coarsen and truncate, then measure again (6')
# - [ ] 5 · The risk table (2')
# - [ ] ✱ Stretch · Which patients stay unique after coarsening, and why

# %%
import os, sys, subprocess
from pathlib import Path

IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    REPO_URL = "https://github.com/SDAIAAcademy/ds-405.git"
    if not Path("/content/ds-405").exists():
        subprocess.run(["git", "clone", "-q", REPO_URL, "/content/ds-405"], check=True)
    os.chdir("/content/ds-405/labs")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements-colab.txt"], check=True)
else:
    while not Path("rimah.py").exists() and Path.cwd() != Path.cwd().parent:
        os.chdir("..")  # solutions/ notebooks run from labs/
sys.path.insert(0, os.getcwd())

import polars as pl
import rimah as U
