
# %%
import pandas as pd

# The GIAS extract is Windows-encoded, which is why raw bytes looked odd earlier.
df = pd.read_csv("data/raw/GIAS.csv", encoding="cp1252", low_memory=False)

# The filtering block - keep only OPEN establishments in our two boroughs.
boroughs = ["Southwark", "Lambeth"]
sl_schools = df[
    df["LA (name)"].isin(boroughs)
    & (df["EstablishmentStatus (name)"] == "Open")
].copy()

# Exclude provision not relevant (post-16 and adult education).
exclude = [
    "Higher education institutions",
    "Further education",
    "Special post 16 institution",
    "Free schools 16 to 19",
    "Academy 16 to 19 sponsor led",
]
# Keep rows whose type is NOT in the exclude list (~ inverts the mask).
sl_schools = sl_schools[~sl_schools["TypeOfEstablishment (name)"].isin(exclude)].copy()

# Convert age to numbers; anything unconvertible becomes NaN instead of raising an error.
sl_schools["StatutoryLowAge"] = pd.to_numeric(sl_schools["StatutoryLowAge"], errors="coerce")

# Pre-reception provision: has nursery classes, OR admits children aged 3 or under.
sl_schools["has_pre_reception_provision"] = (
    (sl_schools["NurseryProvision (name)"] == "Has Nursery Classes")
    | (sl_schools["StatutoryLowAge"] <= 3)
)

early = sl_schools[sl_schools["has_pre_reception_provision"]].copy()

print(len(sl_schools), "open schools;", len(early), "with early-years provision")

# Create a .csv file in the ‘processed’ folder.
sl_schools.to_csv("data/processed/southwark_lambeth_schools.csv", index=False)

# %%
ofsted = pd.read_excel(
    "data/raw/ofsted_childcare_2026-03.ods",
    engine="odf",
    sheet_name="D1_Childcare_providers",
    skiprows=3,
)
print(ofsted.shape)

# %%
# Ofsted slice: active Early Years Register providers in our two boroughs.
sl_childcare = ofsted[
    ofsted["Local authority"].isin(boroughs)
    & (ofsted["Provider Early Years Register flag"] == "Y")
].copy()
print(len(sl_childcare), "EYR providers in Southwark & Lambeth")
print(sl_childcare["Provider type"].value_counts())

# Create a .csv file in the ‘processed’ folder.
sl_childcare.to_csv("data/processed/southwark_lambeth_childcare.csv", index=False)

# %%
