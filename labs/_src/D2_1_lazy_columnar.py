# /// script
# requires-python = ">=3.12"
# dependencies = ["polars>=2.0", "pyyaml>=6.0", "psutil>=7.0"]
# ///
# %% [markdown]
# # Lab 2.1 · From eager to lazy
#
# Day 2 · Session 1 (Columnar files and lazy execution) · 25 min.
#
# Rewrite an eager cleaning script as a lazy query over the partitioned lake and compare time, peak memory and the result.
#
# **Tasks**
# - [ ] 1 · Run the eager script and measure it (5')
# - [ ] 2 · Read the lake's partitions and the query plan (5')
# - [ ] 3 · Write the lazy query (8')
# - [ ] 4 · Same result, less time and memory (4')
# - [ ] 5 · Streaming for the full size (3')
# - [ ] ✱ Stretch · The same query in DuckDB SQL over the same files

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
