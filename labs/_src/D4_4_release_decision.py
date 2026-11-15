# /// script
# requires-python = ">=3.12"
# dependencies = ["polars>=2.0", "pyyaml>=6.0", "psutil>=7.0"]
# ///
# %% [markdown]
# # Lab 4.4 · The decision for the university
#
# Day 4 · Session 4 (The release decision) · 25 min.
#
# Draft the decision for the university request (method, residual risk, conditions, approver) from the measured results, and test the request against the national rules for sharing and secondary use.
#
# **Tasks**
# - [ ] 1 · Read the request and the measured results (4')
# - [ ] 2 · Test the request against the sharing principles and secondary-use rules (7')
# - [ ] 3 · Choose the method and state the residual risk (6')
# - [ ] 4 · Conditions and approver (5')
# - [ ] 5 · Validate and write the record (3')
# - [ ] ✱ Stretch · Write the strongest objection and your answer

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
