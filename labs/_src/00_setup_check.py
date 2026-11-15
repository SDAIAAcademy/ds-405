# /// script
# requires-python = ">=3.12"
# dependencies = ["polars>=2.0", "duckdb>=1.4", "deltalake>=1.4", "pyarrow>=20.0", "pandas>=2.2", "numpy>=2.0", "scikit-learn>=1.6", "matplotlib>=3.9", "opendp>=0.16", "pyyaml>=6.0", "psutil>=7.0"]
# ///
# %% [markdown]
# # Setup check
#
# Run this once before Day 1, on your laptop or in Colab. It imports every library the labs use,
# reads one data file, writes and reads a small Delta table, and reports the memory you have. Nothing
# here calls a model or needs a key: this course uses none.

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

# %%
import importlib
missing = []
for name in ["polars", "duckdb", "deltalake", "pyarrow", "pandas", "numpy", "sklearn", "matplotlib", "opendp", "yaml", "psutil"]:
    try:
        m = importlib.import_module(name)
        print(f"{name:12} {getattr(m, '__version__', 'installed')}")
    except ImportError:
        missing.append(name)
print("missing:", missing or "nothing")

# %%
import polars as pl
import psutil
import rimah as U

df = U.load("producers/sidra_encounters.csv")
print("Sidra extract:", df.height, "rows")
d = U.lab_dir("setup")
pl.DataFrame({"x": [1, 2, 3]}).write_delta(str(d / "t"))
print("Delta table read back:", pl.read_delta(str(d / "t")).height, "rows")
print(f"memory: {psutil.virtual_memory().total / 1e9:.1f} GB in total, {psutil.virtual_memory().available / 1e9:.1f} GB free")
print("quick mode:", U.QUICK, "(set RIMAH_QUICK=1 for the small lake on Day 2)")
U.check(not missing, "every library is installed")
