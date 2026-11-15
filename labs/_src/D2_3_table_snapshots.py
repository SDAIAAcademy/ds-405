# /// script
# requires-python = ">=3.12"
# dependencies = ["polars>=2.0", "pyyaml>=6.0", "psutil>=7.0"]
# ///
# %% [markdown]
# # Lab 2.3 · Rebuild last month
#
# Day 2 · Session 3 (Tables with history) · 25 min.
#
# Rebuild last month's analysis set from the table snapshot it was built on, prove it is identical, and measure what later corrections changed.
#
# **Tasks**
# - [ ] 1 · Read the table's history (4')
# - [ ] 2 · The analysis run record (4')
# - [ ] 3 · Rebuild from the recorded version (7')
# - [ ] 4 · Prove it identical, then diff with today (6')
# - [ ] 5 · What vacuuming would break (4')
# - [ ] ✱ Stretch · Restore the table to the recorded version and compare

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
