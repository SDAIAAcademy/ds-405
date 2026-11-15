# /// script
# requires-python = ">=3.12"
# dependencies = ["polars>=2.0", "pyyaml>=6.0", "psutil>=7.0"]
# ///
# %% [markdown]
# # Lab 3.1 · Four requests, three options
#
# Day 3 · Session 1 (When synthetic data fits) · 25 min.
#
# For four data requests, decide between synthetic data, a de-identified extract and a query service, with the evidence for each decision measured on the study tables.
#
# **Tasks**
# - [ ] 1 · Read the four requests and what each needs (4')
# - [ ] 2 · What a synthetic file gets wrong: rare cells (7')
# - [ ] 3 · What an extract leaks: unique records (6')
# - [ ] 4 · The decision table with residual risk (8')
# - [ ] ✱ Stretch · Price each option in staff days and compute

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
