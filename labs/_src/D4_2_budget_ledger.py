# /// script
# requires-python = ">=3.12"
# dependencies = ["polars>=2.0", "pyyaml>=6.0", "psutil>=7.0"]
# ///
# %% [markdown]
# # Lab 4.2 · Twelve months, one budget
#
# Day 4 · Session 2 (Privacy budgets over many releases) · 25 min.
#
# Allocate one privacy budget across twelve monthly readmission statistics with a ledger, plot error against budget, and show why a re-release must be charged.
#
# **Tasks**
# - [ ] 1 · The privacy unit and the contribution bound (5')
# - [ ] 2 · The ledger that refuses to overspend (6')
# - [ ] 3 · Twelve releases under two allocations (6')
# - [ ] 4 · Error against budget (5')
# - [ ] 5 · The averaging attack on free re-releases (3')
# - [ ] ✱ Stretch · The same releases with Gaussian noise under zero-concentrated accounting

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
