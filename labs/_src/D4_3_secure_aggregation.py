# /// script
# requires-python = ">=3.12"
# dependencies = ["polars>=2.0", "pyyaml>=6.0", "psutil>=7.0"]
# ///
# %% [markdown]
# # Lab 4.3 · A pooled rate without pooled records
#
# Day 4 · Session 3 (Analysis without pooling records) · 25 min.
#
# Compute the cross-site readmission rate with a simulated secure-aggregation protocol, handle a site that drops out, and find what the result still discloses.
#
# **Tasks**
# - [ ] 1 · Each site's counts, kept at the site (4')
# - [ ] 2 · Additive secret shares (7')
# - [ ] 3 · Pairwise masks and the aggregator's view (6')
# - [ ] 4 · A site drops out (5')
# - [ ] 5 · What the total still reveals (3')
# - [ ] ✱ Stretch · Add noise to the total before it leaves the aggregator

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
