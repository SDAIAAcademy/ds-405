# /// script
# requires-python = ">=3.12"
# dependencies = ["polars>=2.0", "pyyaml>=6.0", "psutil>=7.0"]
# ///
# %% [markdown]
# # Lab 3.3 · Train on synthetic, test on real
#
# Day 3 · Session 3 (Utility is measured against the analysis) · 25 min.
#
# Train the readmission model on each synthetic dataset, test it on real holdout data, and compare with fidelity scores and the study's own estimate.
#
# **Tasks**
# - [ ] 1 · Fidelity: marginals and correlations (6')
# - [ ] 2 · Train on real, test on real: the reference (5')
# - [ ] 3 · Train on synthetic, test on real (7')
# - [ ] 4 · The study's estimate on each dataset (4')
# - [ ] 5 · The utility report (3')
# - [ ] ✱ Stretch · Which feature's importance moved most, and why

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
