# /// script
# requires-python = ">=3.12"
# dependencies = ["polars>=2.0", "pyyaml>=6.0", "psutil>=7.0"]
# ///
# %% [markdown]
# # Lab 3.2 · Two generators for related tables
#
# Day 3 · Session 2 (Generating related tables) · 25 min.
#
# Fit two generators to the patient and encounter tables, an independent baseline and a hierarchical copula that keeps the parent-child relation, and check what each kept.
#
# **Tasks**
# - [ ] 1 · The relation: encounters per patient (4')
# - [ ] 2 · Baseline: each column on its own (5')
# - [ ] 3 · The copula: parents with their child counts (7')
# - [ ] 4 · Children conditioned on their parent (6')
# - [ ] 5 · Integrity and relation checks (3')
# - [ ] ✱ Stretch · Fit SDV's HMASynthesizer to the same tables in Colab

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
