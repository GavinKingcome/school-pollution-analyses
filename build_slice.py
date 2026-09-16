# %%
"""
build_slice.py

Builds the Southwark and Lambeth slices of two source datasets:

  1. GIAS   - Get Information About Schools (Department for Education)
  2. Ofsted - childcare providers on the Early Years Register

Writes two CSV files into data/processed/.

Written as interactive cells (# %%), so run it one cell at a time and the
tables stay alive for poking at afterwards.

The checks are there to FAIL LOUDLY. If a source file changes shape between
releases, a cell stops with a clear message rather than quietly producing a
wrong answer. A failing cell raises an exception, so the kernel stays alive.
"""

from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------
# Settings. Everything I might want to change lives in this cell.
# ---------------------------------------------------------------------

RAW = Path("data/raw")
PROCESSED = Path("data/processed")

GIAS_FILE = RAW / "GIAS.csv"
OFSTED_FILE = RAW / "ofsted_childcare_2026-03.ods"
OFSTED_SHEET = "D1_Childcare_providers"
OFSTED_SKIPROWS = 3

BOROUGHS = ["Southwark", "Lambeth"]

# Provision aimed at students aged 16 and over. Not relevant to under-5s.
EXCLUDE_TYPES = [
    "Higher education institutions",
    "Further education",
    "Special post 16 institution",
    "Free schools 16 to 19",
    "Academy 16 to 19 sponsor led",
]

# Columns the GIAS logic depends on. Absence of any of these is fatal.
GIAS_REQUIRED = [
    "LA (name)",
    "EstablishmentStatus (name)",
    "TypeOfEstablishment (name)",
    "NurseryProvision (name)",
    "StatutoryLowAge",
]

# Columns the Ofsted filter depends on. Absence of any of these is fatal.
OFSTED_REQUIRED = [
    "Local authority",
    "Provider Early Years Register flag",
]

# Columns where Ofsted writes the literal text "REDACTED" for home-based
# providers. Absence of any of these is a warning, not a fatal error.
REDACTED_COLS = [
    "Provider address line 1",
    "Provider address line 2",
    "Provider address line 3",
    "Provider town",
    "Telephone number",
    "Postcode",
    "Provider name",
    "Registered person name",
    "Registered person URN",
]

# Exact values the filters match on. Checked against the data at run time.
STATUS_OPEN = "Open"
HAS_NURSERY_CLASSES = "Has Nursery Classes"
EYR_FLAG_YES = "Y"

PRE_RECEPTION_MAX_AGE = 3

# Rough floors, to catch a filter that has silently emptied out.
# Set these from your first good run, a little below the real figures.
MIN_SCHOOLS = 180
MIN_CHILDCARE = 550

PROCESSED.mkdir(parents=True, exist_ok=True)


# %%
# ---------------------------------------------------------------------
# Checks. At the start of each session run this cell once before the cells below,  then the cells below can use them.
# ---------------------------------------------------------------------

class DataCheckError(Exception):
    """Raised when a source file is not what the script expects."""


def fail(message):
    """Stop the current cell with a clear message. Kernel stays alive."""
    raise DataCheckError(message)


def warn(message):
    print(f"WARNING: {message}")


def ok(message):
    print(f"  ok: {message}")


def tidy_columns(df):
    """Strip stray whitespace from column names. Headers typed by hand
    often carry a trailing space that is invisible but breaks lookups."""
    df.columns = df.columns.str.strip()
    return df


def require_columns(df, required, source_name):
    """Stop if any column the logic depends on is missing."""
    missing = [c for c in required if c not in df.columns]
    if missing:
        fail(
            f"{source_name} is missing expected column(s): {missing}\n"
            f"The file layout has probably changed. "
            f"Columns actually present:\n{sorted(df.columns)}"
        )
    ok(f"{source_name}: all {len(required)} required columns present")


def require_values(df, column, expected, source_name):
    """Stop if a value the filter matches on no longer appears in the column.

    This catches the dangerous case: the column still exists, so there is no
    KeyError, but the values inside it have been reworded and the filter now
    matches nothing.
    """
    present = set(df[column].dropna().unique())
    missing = [v for v in expected if v not in present]
    if missing:
        fail(
            f"{source_name}: value(s) {missing} not found in '{column}'.\n"
            f"The filter would match nothing. "
            f"Values actually present: {sorted(present)[:20]}"
        )
    ok(f"{source_name}: '{column}' contains the expected value(s)")


def require_rows(df, minimum, label):
    """Stop if a result is empty or implausibly small."""
    if len(df) == 0:
        fail(f"{label} came out empty. A filter above is wrong.")
    if len(df) < minimum:
        fail(
            f"{label} has only {len(df)} rows, below the expected floor of "
            f"{minimum}. Check the filters before trusting this."
        )
    ok(f"{label}: {len(df)} rows")


def require_file(path):
    if not path.exists():
        fail(f"Input file not found: {path.resolve()}")


# %%
# ---------------------------------------------------------------------
# GIAS: load and check.
# ---------------------------------------------------------------------
require_file(GIAS_FILE)

# The GIAS extract is Windows-encoded (cp1252), not UTF-8.
df = pd.read_csv(GIAS_FILE, encoding="cp1252", low_memory=False)
df = tidy_columns(df)
print(f"loaded {len(df)} rows, {len(df.columns)} columns")

require_columns(df, GIAS_REQUIRED, "GIAS")
require_values(df, "LA (name)", BOROUGHS, "GIAS")
require_values(df, "EstablishmentStatus (name)", [STATUS_OPEN], "GIAS")
require_values(df, "NurseryProvision (name)", [HAS_NURSERY_CLASSES], "GIAS")


# %%
# ---------------------------------------------------------------------
# GIAS: filter to open schools in our two boroughs.
# ---------------------------------------------------------------------
sl_schools = df[
    df["LA (name)"].isin(BOROUGHS)
    & (df["EstablishmentStatus (name)"] == STATUS_OPEN)
].copy()

# Drop post-16 and adult provision. ~ inverts the mask.
sl_schools = sl_schools[
    ~sl_schools["TypeOfEstablishment (name)"].isin(EXCLUDE_TYPES)
].copy()

require_rows(sl_schools, MIN_SCHOOLS, "open schools in Southwark & Lambeth")


# %%
# ---------------------------------------------------------------------
# GIAS: flag pre-reception provision.
# ---------------------------------------------------------------------
# Ages must be numbers before we can compare them.
# errors="coerce" turns anything unconvertible into NaN.
ages = pd.to_numeric(sl_schools["StatutoryLowAge"], errors="coerce")
unreadable = ages.isna().sum()
if unreadable:
    warn(
        f"{unreadable} school(s) have no readable StatutoryLowAge. "
        f"They cannot qualify on the age test."
    )
sl_schools["StatutoryLowAge"] = ages

# Pre-reception: has nursery classes, OR admits children aged 3 or under.
has_nursery = sl_schools["NurseryProvision (name)"] == HAS_NURSERY_CLASSES
low_age = sl_schools["StatutoryLowAge"] <= PRE_RECEPTION_MAX_AGE
sl_schools["has_pre_reception_provision"] = has_nursery | low_age

early = sl_schools[sl_schools["has_pre_reception_provision"]].copy()

# Show what each half of the OR contributes. If one side ever drops to zero,
# that test has stopped working, and the total would still look plausible.
print(
    f"pre-reception: {has_nursery.sum()} by nursery flag, "
    f"{low_age.sum()} by age, "
    f"{(has_nursery & low_age).sum()} by both, "
    f"{len(early)} in total"
)
if has_nursery.sum() == 0 or low_age.sum() == 0:
    warn("one half of the OR matched nothing - check both columns")

print(len(sl_schools), "open schools;", len(early), "with pre-reception provision")


# %%
# ---------------------------------------------------------------------
# GIAS: save.
# ---------------------------------------------------------------------
schools_out = PROCESSED / "southwark_lambeth_schools.csv"
sl_schools.to_csv(schools_out, index=False)
print(f"wrote {len(sl_schools)} rows -> {schools_out}")


# %%
# ---------------------------------------------------------------------
# Ofsted: load and check.
# ---------------------------------------------------------------------
require_file(OFSTED_FILE)

ofsted = pd.read_excel(
    OFSTED_FILE,
    engine="odf",
    sheet_name=OFSTED_SHEET,
    skiprows=OFSTED_SKIPROWS,
)
ofsted = tidy_columns(ofsted)
print(ofsted.shape)

# If skiprows is wrong, the headers are junk. Unnamed columns are the tell.
unnamed = [c for c in ofsted.columns if str(c).startswith("Unnamed")]
if len(unnamed) > len(ofsted.columns) / 2:
    fail(
        f"Most columns are unnamed. OFSTED_SKIPROWS ({OFSTED_SKIPROWS}) "
        f"is probably wrong for this release."
    )

require_columns(ofsted, OFSTED_REQUIRED, "Ofsted")
require_values(ofsted, "Local authority", BOROUGHS, "Ofsted")
require_values(
    ofsted, "Provider Early Years Register flag", [EYR_FLAG_YES], "Ofsted"
)


# %%
# ---------------------------------------------------------------------
# Ofsted: active Early Years Register providers in our two boroughs.
# ---------------------------------------------------------------------
sl_childcare = ofsted[
    ofsted["Local authority"].isin(BOROUGHS)
    & (ofsted["Provider Early Years Register flag"] == EYR_FLAG_YES)
].copy()

require_rows(sl_childcare, MIN_CHILDCARE, "EYR providers in Southwark & Lambeth")
print(len(sl_childcare), "EYR providers in Southwark & Lambeth")
print(sl_childcare["Provider type"].value_counts())


# %%
# ---------------------------------------------------------------------
# Ofsted: turn withheld/REDACTED details into real missing values.
# ---------------------------------------------------------------------
# Ofsted publishes withheld home-based details as the text "REDACTED".
# Convert to real missing values so isna() and geocoding treat them as absent.
# A missing column here is a warning, not a fatal error.
missing_cols = [c for c in REDACTED_COLS if c not in sl_childcare.columns]
if missing_cols:
    warn(
        f"redacted columns not found, so not cleaned: {missing_cols}\n"
        f"           any REDACTED text in them will survive."
    )

present_cols = [c for c in REDACTED_COLS if c in sl_childcare.columns]
sl_childcare[present_cols] = sl_childcare[present_cols].replace("REDACTED", pd.NA)

# How much address data is actually usable for geocoding.
if "Postcode" in sl_childcare.columns:
    usable = sl_childcare["Postcode"].notna().sum()
    print(
        f"postcodes: {usable} usable, "
        f"{len(sl_childcare) - usable} withheld or missing"
    )

# Catch any REDACTED text left in columns not on the list.
leftover = sl_childcare.isin(["REDACTED"]).sum().sum()
if leftover:
    warn(f"{leftover} 'REDACTED' value(s) remain in columns not listed")


# %%
# ---------------------------------------------------------------------
# Ofsted: save.
# ---------------------------------------------------------------------
childcare_out = PROCESSED / "southwark_lambeth_childcare.csv"
sl_childcare.to_csv(childcare_out, index=False)
print(f"wrote {len(sl_childcare)} rows -> {childcare_out}")