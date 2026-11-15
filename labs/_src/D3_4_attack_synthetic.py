# /// script
# requires-python = ">=3.12"
# dependencies = ["polars>=2.0", "pyyaml>=6.0", "psutil>=7.0"]
# ///
# %% [markdown]
# # Lab 3.4 · Attack each synthetic table
#
# Day 3 · Session 4 (Privacy is measured by attack) · 25 min.
#
# Run distance-to-closest-record and membership-inference tests on each synthetic table, including a vendor's file, and write the attack report.
#
# **Tasks**
# - [ ] 1 · Distances to train and to holdout (6')
# - [ ] 2 · Distance to closest record, per table (6')
# - [ ] 3 · Membership inference and its AUC (7')
# - [ ] 4 · The vendor file (3')
# - [ ] 5 · The attack report (3')
# - [ ] ✱ Stretch · Attack the linked patient histories, not single rows

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
