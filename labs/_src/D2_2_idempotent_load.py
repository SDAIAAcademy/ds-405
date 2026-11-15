# /// script
# requires-python = ">=3.12"
# dependencies = ["polars>=2.0", "pyyaml>=6.0", "psutil>=7.0"]
# ///
# %% [markdown]
# # Lab 2.2 · Load one day twice
#
# Day 2 · Session 2 (Incremental and idempotent loads) · 25 min.
#
# Make the daily laboratory load idempotent and prove it by loading one day twice, including a day the producer delivered again with corrections.
#
# **Tasks**
# - [ ] 1 · The append load and its duplicates (5')
# - [ ] 2 · A table fingerprint (4')
# - [ ] 3 · Idempotent: overwrite the day's partition (6')
# - [ ] 4 · Corrections: merge on the business key (6')
# - [ ] 5 · Load every day twice and compare (4')
# - [ ] ✱ Stretch · Keep a load log so a day is skipped when its file has not changed

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
