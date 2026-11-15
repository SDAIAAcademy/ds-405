# /// script
# requires-python = ">=3.12"
# dependencies = ["polars>=2.0", "numpy>=2.0", "opendp>=0.12", "pyyaml>=6.0", "psutil>=7.0"]
# ///
# %% [markdown]
# # Lab 4.3 · A pooled rate without pooled records
#
# Day 4 · Session 3 (Analysis without pooling records) · 25 min.
#
# Compute the cross-site readmission rate with a simulated secure-aggregation protocol, handle a site that drops out, and find what the result still discloses.
#
# **Reference state.** The study's stays (`data/study/`), split by the hospital group that
# treated each patient: Sidra, Ufuq and Rawdah each hold only their own. Suppose the three groups
# will not send records to the consortium for this question; they will send numbers. The
# protocol is simulated in one notebook: each "site" is a function that sees only its own data
# and the messages addressed to it. Everything is written under `artifacts/D4_3/`.
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

import secrets

import numpy as np
import polars as pl
import rimah as U

WORK = U.lab_dir("D4_3")
P = 2**61 - 1  # all arithmetic is modulo this prime: a share is a uniformly random number below P
SITES = ["SDR", "UFQ", "RWD"]
pts = pl.concat([U.study("train")[0], U.study("holdout")[0]])
enc = pl.concat([U.study("train")[1], U.study("holdout")[1]]).join(pts.select("study_id", "site"), on="study_id")
SITE_DATA = {s: enc.filter(pl.col("site") == s) for s in SITES}  # each site holds only its own rows

# %% [markdown]
# ## 1 · Each site's counts, kept at the site (4')
#
# The pooled rate needs two sums: readmitted stays and stays. Each site computes its own.

# %%
def local_counts(site: str) -> dict:
    d = SITE_DATA[site]
    return {"readmitted": int(d["readmit_30d"].sum()), "stays": d.height}


site_counts = {s: local_counts(s) for s in SITES}
for s, c in site_counts.items():
    print(f"{s}: {c['readmitted']} of {c['stays']} stays readmitted ({c['readmitted'] / c['stays']:.1%})  ← stays at the site")
truth = {k: sum(c[k] for c in site_counts.values()) for k in ["readmitted", "stays"]}

# %% [markdown]
# ## 2 · Additive secret shares (7')
#
# Split a number x into n random shares that add up to x modulo P. Any n − 1 shares are uniformly
# random and say nothing about x. Each site splits its count and sends one share to each site;
# each site adds the shares it received and publishes only that sum; the sums add up to the total.
#
# ✏️ **Exercise** · `share(x, n)`: n − 1 random numbers below P (use `secrets.randbelow`), and a
# last share that makes the total x modulo P. `reconstruct(shares)` is their sum modulo P.

# %%
def share(x: int, n: int) -> list[int]:
    # BEGIN SOLUTION
    parts = [secrets.randbelow(P) for _ in range(n - 1)]
    return parts + [(x - sum(parts)) % P]
    # END SOLUTION


def reconstruct(shares: list[int]) -> int:
    # BEGIN SOLUTION
    return sum(shares) % P
    # END SOLUTION


# %%
try:
    share(1, 3); reconstruct([1])
except NotImplementedError:
    def share(x, n):
        parts = [secrets.randbelow(P) for _ in range(n - 1)]
        return parts + [(x - sum(parts)) % P]

    def reconstruct(shares):
        return sum(shares) % P
    print("Exercise not done: using the reference functions.")

outbox = {s: share(site_counts[s]["readmitted"], len(SITES)) for s in SITES}           # site s → share j to site j
inbox = {j: [outbox[s][i] for s in SITES] for i, j in enumerate(SITES)}               # what site j receives
partial = {j: reconstruct(inbox[j]) for j in SITES}                                   # published by site j
print("what site UFQ received:", inbox["UFQ"])
print("partial sums published:", partial)
pooled_readmitted = reconstruct(list(partial.values()))
U.check(pooled_readmitted == truth["readmitted"], f"the partial sums add up to the true total ({pooled_readmitted})")

# %% [markdown]
# ## 3 · Pairwise masks and the aggregator's view (6')
#
# With many sites, every-to-every shares are costly. Practical secure aggregation (Bonawitz et
# al., 2017) uses **pairwise masks**: each pair of sites agrees on a random mask m; the site
# first in order adds it, the other subtracts it. The aggregator sees masked numbers only; the
# masks cancel in the sum.
#
# ✏️ **Exercise** · `masked(site, x, masks)`: x plus the masks shared with later sites, minus
# those shared with earlier sites, modulo P. `masks[(a, b)]` holds the mask of the pair a < b in
# the order of `SITES`.

# %%
def agree_masks(sites: list[str]) -> dict:
    """Each pair agrees on a random mask (in practice by key agreement; simulated here)."""
    return {(a, b): secrets.randbelow(P) for i, a in enumerate(sites) for b in sites[i + 1:]}


def masked(site: str, x: int, masks: dict) -> int:
    # BEGIN SOLUTION
    y = x
    for (a, b), m in masks.items():
        if a == site:
            y += m
        elif b == site:
            y -= m
    return y % P
    # END SOLUTION


# %%
masks = agree_masks(SITES)
try:
    masked(SITES[0], 0, masks)
except NotImplementedError:
    def masked(site, x, masks):
        y = x + sum(m for (a, b), m in masks.items() if a == site) - sum(m for (a, b), m in masks.items() if b == site)
        return y % P
    print("Exercise not done: using the reference function.")
pooled = {}
for key in ["readmitted", "stays"]:
    seen = {s: masked(s, site_counts[s][key], masks) for s in SITES}  # all the aggregator receives
    pooled[key] = sum(seen.values()) % P
print("the aggregator's view of the readmitted counts:", {s: masked(s, site_counts[s]["readmitted"], masks) for s in SITES})
U.check(pooled["readmitted"] == truth["readmitted"] and pooled["stays"] == truth["stays"], "the masks cancel: the totals are exact")
pooled["rate"] = round(pooled["readmitted"] / pooled["stays"], 4)
print(f"pooled 30-day readmission rate: {pooled['rate']:.2%} ({pooled['readmitted']} of {pooled['stays']} stays)")

# %% [markdown]
# ## 4 · A site drops out (5')
#
# Rawdah agreed its masks, then lost its connection before sending. The two masked values that
# arrive no longer add up: Rawdah's masks are left in. The protocol's answer: the surviving sites
# reveal the masks they shared **with the dropped site** (in the real protocol, recovered from
# secret shares of each site's mask seeds), and the aggregator removes them.

# %%
alive = ["SDR", "UFQ"]
seen = {s: masked(s, site_counts[s]["readmitted"], masks) for s in alive}
broken = sum(seen.values()) % P
print(f"sum of the two masked values: {broken} (true sum of the two sites: {sum(site_counts[s]['readmitted'] for s in alive)})")


def remove_dropped(total: int, dropped: str, masks: dict) -> int:
    # BEGIN SOLUTION
    for (a, b), m in masks.items():
        if b == dropped and a in alive:
            total -= m      # a added m for its later partner
        elif a == dropped and b in alive:
            total += m      # b subtracted m for its earlier partner
    return total % P
    # END SOLUTION


try:
    recovered = remove_dropped(broken, "RWD", masks)
except NotImplementedError:
    recovered = sum(site_counts[s]["readmitted"] for s in alive)
U.check(recovered == sum(site_counts[s]["readmitted"] for s in alive), f"after removing Rawdah's masks: {recovered}, the two surviving sites' total")

# %% [markdown]
# 🔍 Recovery reveals the dropped site's masks. If Rawdah's value then arrives late, the aggregator
# could unmask it alone: the protocol must refuse late values once recovery has started.

# %% [markdown]
# ## 5 · What the total still reveals (3')
#
# Secure aggregation hides the inputs from the aggregator, not from the arithmetic. Two cases:

# %%
rwd_inferred = pooled["readmitted"] - site_counts["SDR"]["readmitted"] - site_counts["UFQ"]["readmitted"]
print(f"Sidra and Ufuq together know their own counts: total − theirs = Rawdah's count exactly ({rwd_inferred})")
U.check(rwd_inferred == site_counts["RWD"]["readmitted"], "two colluding sites learn the third's input from the total")
small = enc.filter(pl.col("dx_group") == "obstetric", pl.col("readmit_30d") == 1).group_by("site").len().sort("site")
print("obstetric readmissions by site (each site knows only its own row):")
U.show(small)
sub = dict(small.rows())
print(f"published subgroup total {sum(sub.values())}; Sidra and Ufuq subtract theirs: Rawdah had {sum(sub.values()) - sub["SDR"] - sub["UFQ"]} obstetric stays followed by readmission")
print("a count that small points at one or two people a colleague may know")

# %% [markdown]
# 🔍 The pooled output needs its own protection: minimum numbers of sites and of people per cell,
# and noise on the total (Lab 4.2's budget) when it is published.

# %% [markdown]
# ## ✱ Stretch · Add noise to the total before it leaves the aggregator
#
# Add Laplace noise with ε = 0.5 (contribution bound: one stay changes the readmitted count by 1)
# to the pooled readmitted count before publication. How much does the rate move? Does it still
# stop the two-colluding-sites inference?

# %%
import opendp.prelude as dp
dp.enable_features("contrib")
noisy = dp.m.make_laplace(dp.atom_domain(T=int), dp.absolute_distance(T=int), scale=2.0)
published = noisy(int(pooled["readmitted"]))
print(f"published readmitted {published} (true {pooled['readmitted']}), rate {published / pooled['stays']:.2%}")
print(f"the colluding sites' estimate of Rawdah: {published - site_counts['SDR']['readmitted'] - site_counts['UFQ']['readmitted']} ± about 2")
U.save_json({"site_counts_kept_at_sites": True, "pooled": pooled}, WORK / "pooled.json")

# %% [markdown]
# ## Checkpoint
#
# 1. What does the aggregator see in the pairwise-mask protocol?
# 2. Why must late values be refused after a dropout recovery?
# 3. The protocol is secure. Why can the pooled count still disclose a site's count?
#
# <details><summary>Answers</summary>
#
# 1. One uniformly random-looking number per site; only their sum means anything.
# 2. Recovery revealed the dropped site's masks; its late masked value could then be unmasked alone.
# 3. Secure aggregation protects inputs during computation; the output is exact, and anyone who knows all inputs but one can subtract.
# </details>
#
# **Carry forward.** `pooled.json`.
