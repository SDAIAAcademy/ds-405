# /// script
# requires-python = ">=3.12"
# dependencies = ["polars>=2.0", "numpy>=2.0", "scikit-learn>=1.6", "pyyaml>=6.0", "opendp>=0.16"]
# ///
"""Writes the synthetic data of the Rimah Health Data Consortium into labs/data/.

    uv run python prepare_data.py           # everything committed with the course
    uv run python prepare_data.py --check   # write to a temporary folder and compare

Fixed seed (405): the same bytes on every run. Every person, identifier and record is synthetic.
National identifiers are random ten-digit strings planted for the linkage lab; they belong to no one.

What it writes
  producers/   three encounter extracts in each producer's own format (Day 1), a delivery manifest,
               Ufuq's version 2 sample (Lab 1.4)
  truth/       the planted truth: which local patient is which person (Lab 1.3)
  study/       pseudonymised study tables: patients and encounters, train and holdout (Days 3 and 4)
  study/synthetic/  reference synthetic tables of two generators and a vendor's file (_tools/synth_reference.py)
  reference/   reference results for the safety-net cells, computed here from the planted answers
The partitioned lake of Day 2 is not committed: rimah_lake.py writes it on demand.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
SEED = 405

FIRST_M = ["Abdulrahman", "Abdullah", "Mohammed", "Fahad", "Khalid", "Saud", "Turki", "Faisal", "Nasser", "Omar",
           "Yousef", "Ibrahim", "Saleh", "Majed", "Hamad", "Sultan", "Bandar", "Waleed", "Ziyad", "Abdulaziz"]
FIRST_F = ["Noura", "Sara", "Reem", "Lama", "Hessa", "Maha", "Amal", "Mona", "Huda", "Asma",
           "Latifa", "Jawaher", "Shahad", "Ghada", "Hind", "Nouf", "Abeer", "Dalal", "Lujain", "Wafa"]
FAMILY = ["Al-Harbi", "Al-Otaibi", "Al-Qahtani", "Al-Ghamdi", "Al-Zahrani", "Al-Dosari", "Al-Shehri", "Al-Mutairi",
          "Al-Anazi", "Al-Shammari", "Al-Subaie", "Al-Juhani", "Al-Malki", "Al-Rashidi", "Al-Yami", "Al-Shahrani",
          "Al-Asiri", "Al-Balawi", "Al-Harthi", "Al-Qarni"]
DX = {  # ICD-10 code: (group, weight)
    "I50.9": ("cardio", 9), "I21.4": ("cardio", 4), "I63.9": ("cardio", 4), "N18.3": ("renal", 6), "N39.0": ("renal", 5),
    "E11.9": ("metabolic", 7), "J44.1": ("respiratory", 6), "J18.9": ("respiratory", 8), "A41.9": ("infection", 5),
    "K35.8": ("surgical", 5), "S72.0": ("surgical", 4), "K80.2": ("surgical", 4), "O80": ("obstetric", 8), "C34.9": ("other", 2),
}
WARD_FOR = {"cardio": "CARD", "renal": "MED", "metabolic": "MED", "respiratory": "MED", "infection": "ICU",
            "surgical": "SURG", "obstetric": "OBS", "other": "MED"}
DISPO = ["HOME", "TRANSFER", "DIED", "LAMA"]
REGIONS = ["Riyadh", "Makkah", "Eastern", "Qassim", "Asir", "Jazan", "Tabuk"]


# ================================================================ people (the planted truth)
def make_people(rng: np.random.Generator, n: int = 9000) -> pl.DataFrame:
    sex = rng.choice(["M", "F"], size=n)
    first = np.where(sex == "M", rng.choice(FIRST_M, size=n), rng.choice(FIRST_F, size=n))
    family = rng.choice(FAMILY, size=n)
    start = dt.date(1940, 1, 1).toordinal()
    dob = [dt.date.fromordinal(int(start + d)) for d in rng.integers(0, 365 * 65, size=n)]
    nid = [("1" if rng.random() < 0.72 else "2") + "".join(map(str, rng.integers(0, 10, size=9))) for _ in range(n)]
    people = pl.DataFrame({"person_id": [f"P{i:05d}" for i in range(1, n + 1)], "national_id": nid,
                           "first": first, "family": family, "birth_date": dob, "sex": sex})
    # 40 look-alike pairs: a second person with the same name, birth date and sex (a real hazard of name keys)
    idx = rng.choice(n // 2, size=40, replace=False)
    twins = rng.choice(np.arange(n // 2, n), size=40, replace=False)
    first_l, family_l, dob_l, sex_l = (people[c].to_list() for c in ["first", "family", "birth_date", "sex"])
    for a, b in zip(idx, twins):
        first_l[b], family_l[b], dob_l[b], sex_l[b] = first_l[a], family_l[a], dob_l[a], sex_l[a]
    return people.with_columns(pl.Series("first", first_l), pl.Series("family", family_l),
                               pl.Series("birth_date", dob_l), pl.Series("sex", sex_l))


def make_encounters(rng: np.random.Generator, people: pl.DataFrame) -> pl.DataFrame:
    """Q4 2025 encounters with producers; some people visit two or three groups."""
    n = people.height
    home = rng.choice(["SDR", "UFQ", "RWD"], size=n, p=[0.36, 0.34, 0.30])
    rows = []
    q_start = dt.date(2025, 10, 1).toordinal()
    codes = list(DX)
    w = np.array([DX[c][1] for c in codes], float)
    w /= w.sum()
    for i in range(n):
        if rng.random() > 0.80:  # a third of people have no encounter this quarter
            continue
        sites = [home[i]]
        if rng.random() < 0.22:
            sites.append(rng.choice([s for s in ["SDR", "UFQ", "RWD"] if s != home[i]]))
        if len(sites) == 2 and rng.random() < 0.15:
            sites.append(next(s for s in ["SDR", "UFQ", "RWD"] if s not in sites))
        for site in sites:
            for _ in range(1 + int(rng.random() < 0.18)):
                adm = q_start + int(rng.integers(0, 92))
                los = int(min(40, rng.gamma(2.0, 2.2))) + 1
                code = codes[rng.choice(len(codes), p=w)]
                weight = float(np.clip(rng.normal(78, 17), 38, 190))
                creat = float(np.clip(rng.lognormal(np.log(90), 0.45), 35, 900))
                rows.append({"person_id": people["person_id"][i], "producer": site,
                             "admit_date": dt.date.fromordinal(adm), "discharge_date": dt.date.fromordinal(adm + los),
                             "ward": WARD_FOR[DX[code][0]], "primary_dx": code,
                             "disposition": rng.choice(DISPO, p=[0.86, 0.07, 0.02, 0.05]),
                             "weight_kg": round(weight, 1), "creatinine_umol_l": round(creat, 1)})
    enc = pl.DataFrame(rows)
    # Ufuq's extract stops nine days before the quarter ends (the stale delivery of Lab 1.2)
    enc = enc.filter(~((pl.col("producer") == "UFQ") & (pl.col("admit_date") > dt.date(2025, 12, 22))))
    return enc.sort(["producer", "admit_date", "person_id"])


def name_variant(rng, first: str, family: str) -> tuple[str, str]:
    """A spelling variant a different registration desk would type."""
    k = rng.integers(0, 4)
    if k == 0 and first.startswith("Abdul"):
        return "Abdul " + first[5:], family
    if k == 1:
        return first, family.replace("Al-", "Al ")
    if k == 2:
        return first, family.replace("Al-", "Al")
    return first.upper(), family.upper()


def to_arabic_digits(s: str) -> str:
    return s.translate(str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩"))


def typo(rng, nid: str) -> str:
    i = int(rng.integers(1, 9))
    return nid[:i] + nid[i + 1] + nid[i] + nid[i + 2:] if nid[i] != nid[i + 1] else nid[:i] + str((int(nid[i]) + 1) % 10) + nid[i + 1:]


def write_producers(rng, people: pl.DataFrame, enc: pl.DataFrame, out: Path) -> dict:
    pp = {r["person_id"]: r for r in people.iter_rows(named=True)}
    (out / "producers").mkdir(parents=True, exist_ok=True)
    (out / "truth").mkdir(parents=True, exist_ok=True)
    truth, planted = [], {"ufuq_id_typos": 0, "ufuq_name_variants": 0, "rawdah_name_variants": 0,
                          "ufuq_duplicate_rows": 0, "rawdah_discharge_before_admit": 0}
    local = {}
    seq = {"SDR": 0, "UFQ": 0, "RWD": 0}

    def local_id(site, pid):
        key = (site, pid)
        if key not in local:
            seq[site] += 1
            local[key] = {"SDR": "S", "UFQ": "MRN-", "RWD": "R"}[site] + f"{seq[site]:06d}"
            truth.append({"producer": site, "local_patient_id": local[key], "person_id": pid})
        return local[key]

    ident = {}  # what each producer's registration desk recorded for a person, fixed per (site, person)

    def identity(site, pid):
        key = (site, pid)
        if key in ident:
            return ident[key]
        p = pp[pid]
        nid, first, family = p["national_id"], p["first"], p["family"]
        if site == "UFQ" and rng.random() < 0.015:
            nid = typo(rng, nid)
            planted["ufuq_id_typos"] += 1
        if site in ("UFQ", "RWD") and rng.random() < 0.06:
            first, family = name_variant(rng, first, family)
            planted["ufuq_name_variants" if site == "UFQ" else "rawdah_name_variants"] += 1
        ident[key] = (nid, first, family)
        return ident[key]

    sdr, ufq, rwd = [], [], []
    for r in enc.iter_rows(named=True):
        site, pid = r["producer"], r["person_id"]
        p = pp[pid]
        lid = local_id(site, pid)
        nid, first, family = identity(site, pid)
        if site == "SDR":
            sdr.append({"encounter_id": f"SDR-{len(sdr) + 1:06d}", "patient_id": lid, "national_id": nid,
                        "full_name": f"{first} {family}", "birth_date": p["birth_date"].isoformat(), "sex": p["sex"],
                        "admit_date": r["admit_date"].isoformat(), "discharge_date": r["discharge_date"].isoformat(),
                        "ward": r["ward"], "primary_dx": r["primary_dx"], "disposition": r["disposition"],
                        "weight_kg": r["weight_kg"], "creatinine_umol_l": r["creatinine_umol_l"]})
        elif site == "UFQ":
            shown = nid
            u = rng.random()
            if u < 0.55:
                shown = f"{nid[:4]} {nid[4:7]} {nid[7:]}"
            elif u < 0.63:
                shown = to_arabic_digits(nid)
            ufq.append({"EncounterNo": f"UF{len(ufq) + 70001}", "MRN": lid, "NationalID": shown,
                        "PatientName": f"{first} {family}", "DOB": p["birth_date"].strftime("%d/%m/%Y"),
                        "Gender": {"M": "Male", "F": "Female"}[p["sex"]],
                        "AdmissionDate": r["admit_date"].strftime("%d/%m/%Y"),
                        "DischargeDate": r["discharge_date"].strftime("%d/%m/%Y"),
                        "Department": {"MED": "INT-MED", "SURG": "GEN-SURG", "CARD": "CARDIO", "ICU": "ICU", "OBS": "OBGYN"}[r["ward"]],
                        "DiagnosisCode": r["primary_dx"].replace(".", ""),
                        "DischargeStatus": str(DISPO.index(r["disposition"]) + 1),
                        "WeightKg": r["weight_kg"], "Creatinine_mgdl": round(r["creatinine_umol_l"] / 88.42, 2)})
        else:
            adm, dis = r["admit_date"], r["discharge_date"]
            if rng.random() < 0.008:
                adm, dis = dis, adm  # the planted swap: discharge before admission
                planted["rawdah_discharge_before_admit"] += 1
            rwd.append({"enc_id": f"{len(rwd) + 1:07d}", "pt_id": lid, "nid": "SA-" + nid,
                        "name": f"{first} {family}", "dob": p["birth_date"].strftime("%Y%m%d"),
                        "sex": {"M": "1", "F": "2"}[p["sex"]], "adm_dt": adm.isoformat(), "dis_dt": dis.isoformat(),
                        "unit": {"MED": "M", "SURG": "S", "CARD": "C", "ICU": "I", "OBS": "O"}[r["ward"]],
                        "icd10": r["primary_dx"].lower(), "disp": f"{DISPO.index(r['disposition']) + 1:02d}",
                        "weight_lb": round(r["weight_kg"] * 2.20462, 1), "creat_umol": r["creatinine_umol_l"]})
    # Ufuq sends 37 rows twice
    dup = [ufq[i] for i in sorted(rng.choice(len(ufq), size=37, replace=False))]
    planted["ufuq_duplicate_rows"] = len(dup)
    ufq = ufq + dup
    pl.DataFrame(sdr).write_csv(out / "producers/sidra_encounters.csv")
    pl.DataFrame(ufq).write_csv(out / "producers/ufuq_encounters.csv")
    pl.DataFrame(rwd).write_csv(out / "producers/rawdah_encounters.csv")
    pl.DataFrame(truth).sort(["producer", "local_patient_id"]).write_csv(out / "truth/person_map.csv")
    manifest = {"period": {"from": "2025-10-01", "to": "2025-12-31"},
                "deliveries": [{"producer": "SDR", "file": "sidra_encounters.csv", "delivered_on": "2026-01-02"},
                               {"producer": "UFQ", "file": "ufuq_encounters.csv", "delivered_on": "2025-12-31"},
                               {"producer": "RWD", "file": "rawdah_encounters.csv", "delivered_on": "2026-01-01"}]}
    (out / "producers/manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")

    # Ufuq version 2: what arrived in January without notice
    v2 = pl.DataFrame(ufq[:600]).with_columns(
        pl.col("DOB").str.to_date("%d/%m/%Y").dt.strftime("%Y-%m-%d"),
        (pl.col("Creatinine_mgdl").cast(pl.Float64) * 88.42).round(1).alias("Creatinine"),
        pl.Series("Nationality", rng.choice(["Saudi", "Non-Saudi"], size=600, p=[0.7, 0.3])),
    ).drop("Creatinine_mgdl")
    status = v2["DischargeStatus"].to_list()
    for i in rng.choice(600, size=31, replace=False):
        if status[i] == "1":
            status[i] = "5"  # a new code: discharged to home health care
    v2 = v2.with_columns(pl.Series("DischargeStatus", status))
    cols = [c for c in v2.columns if c != "Nationality"]
    v2.select(cols[:9] + ["Nationality"] + cols[9:]).write_csv(out / "producers/ufuq_v2_sample.csv")
    return planted


# ================================================================ the study tables (Days 3 and 4)
def make_study(rng: np.random.Generator, n: int = 6000) -> tuple[pl.DataFrame, pl.DataFrame]:
    sex = rng.choice(["M", "F"], size=n)
    birth_year = np.clip(np.round(rng.normal(1966, 16, size=n)), 1930, 2006).astype(int)
    age = 2025 - birth_year
    region = rng.choice(REGIONS, size=n, p=[0.30, 0.24, 0.17, 0.09, 0.08, 0.07, 0.05])
    nationality = rng.choice(["Saudi", "Non-Saudi"], size=n, p=[0.74, 0.26])
    diabetes = (rng.random(n) < 0.12 + 0.004 * np.clip(age - 30, 0, 50)).astype(int)
    ckd = (rng.random(n) < 0.03 + 0.003 * np.clip(age - 40, 0, 50) + 0.08 * diabetes).astype(int)
    hf = (rng.random(n) < 0.02 + 0.003 * np.clip(age - 45, 0, 50)).astype(int)
    prior = rng.poisson(0.4 + 0.5 * ckd + 0.6 * hf + 0.01 * np.clip(age - 40, 0, 50))
    site = rng.choice(["SDR", "UFQ", "RWD"], size=n, p=[0.36, 0.34, 0.30])
    n_enc = 1 + rng.poisson(0.9 + 0.7 * ckd + 0.8 * hf + 0.3 * diabetes + 0.15 * np.minimum(prior, 4))
    n_enc = np.minimum(n_enc, 9)
    pts = pl.DataFrame({"study_id": [f"R{i:06d}" for i in range(1, n + 1)], "sex": sex, "birth_year": birth_year,
                        "region": region, "nationality": nationality, "diabetes": diabetes, "ckd": ckd,
                        "heart_failure": hf, "prior_admissions": prior.astype(int), "site": site})
    groups = ["cardio", "renal", "metabolic", "respiratory", "infection", "surgical", "obstetric", "other"]
    rows = []
    for i in range(n):
        months = np.sort(rng.integers(1, 13, size=n_enc[i]))
        for k, m in enumerate(months):
            p = np.array([1 + 3 * hf[i], 1 + 3 * ckd[i], 1 + 2 * diabetes[i], 1.5, 1.2, 1.5,
                          (1.6 if sex[i] == "F" and age[i] < 45 else 0.0), 0.4])
            g = groups[rng.choice(8, p=p / p.sum())]
            los = int(min(45, 1 + rng.gamma(1.6 + 0.6 * hf[i] + 0.5 * ckd[i] + 0.01 * age[i], 2.0)))
            n_meds = int(min(25, rng.poisson(3 + 2 * diabetes[i] + 3 * hf[i] + 2 * ckd[i] + 0.04 * age[i])))
            creat = float(np.clip(rng.lognormal(np.log(80 + 140 * ckd[i]), 0.35), 30, 1200))
            glucose = float(np.clip(rng.lognormal(np.log(6.0 + 3.5 * diabetes[i]), 0.25), 2.5, 35))
            disch = rng.choice(["home", "transfer", "against_advice"], p=[0.88, 0.07, 0.05])
            logit = (-3.1 + 0.55 * hf[i] + 0.35 * ckd[i] + 0.03 * los + 0.05 * ckd[i] * los
                     + 0.28 * min(prior[i], 4) + 0.06 * n_meds + 0.6 * (disch == "against_advice")
                     + 0.35 * (age[i] >= 75) + 0.45 * (k > 0))
            readmit = int(rng.random() < 1 / (1 + np.exp(-logit)))
            rows.append({"study_id": pts["study_id"][i], "enc_seq": k + 1, "admit_month": f"2025-{m:02d}",
                         "los_days": los, "ward": WARD_FOR[g], "dx_group": g, "n_meds": n_meds,
                         "creatinine": round(creat, 1), "glucose": round(glucose, 1), "discharge": disch,
                         "readmit_30d": readmit})
    enc = pl.DataFrame(rows)
    return pts, enc


def split_study(rng, pts: pl.DataFrame) -> pl.DataFrame:
    hold = rng.random(pts.height) < 0.30
    return pts.with_columns(pl.Series("split", np.where(hold, "holdout", "train")))


def write_study(pts: pl.DataFrame, enc: pl.DataFrame, out: Path):
    d = out / "study"
    d.mkdir(parents=True, exist_ok=True)
    for part in ["train", "holdout"]:
        p = pts.filter(pl.col("split") == part).drop("split")
        p.write_parquet(d / f"patients_{part}.parquet")
        enc.join(p.select("study_id"), on="study_id").sort(["study_id", "enc_seq"]).write_parquet(d / f"encounters_{part}.parquet")


def main(out: Path):
    rng = np.random.default_rng(SEED)
    people = make_people(rng)
    enc = make_encounters(rng, people)
    planted = write_producers(rng, people, enc, out)
    srng = np.random.default_rng(SEED + 1)
    pts, senc = make_study(srng, 6000)
    pts = split_study(srng, pts)
    write_study(pts, senc, out)
    sys.path.insert(0, str(HERE / "_tools"))
    import synth_reference
    synth_reference.write_reference_synthetic(out)
    (out / "reference").mkdir(parents=True, exist_ok=True)
    (out / "reference" / "planted.json").write_text(json.dumps(planted, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print("data written:", out)
    print("the safety-net references come from the solutions: uv run python _tools/make_references.py")


if __name__ == "__main__":
    if "--check" in sys.argv:
        import filecmp
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            main(Path(tmp))
            bad = [str(p.relative_to(tmp)) for p in Path(tmp).rglob("*") if p.is_file()
                   and not filecmp.cmp(p, HERE / "data" / p.relative_to(tmp), shallow=False)]
            print("identical" if not bad else f"differs: {bad}")
    else:
        main(HERE / "data")
