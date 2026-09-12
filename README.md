# Development Roadmap & Future Direction

## Vision

The Early Years & School Pollution Monitor aims to become an inner-London, research-grade platform focused on the boroughs where deprivation–pollution relationships are sharpest and most varied. Built initially for Lambeth and Southwark, the platform will scale across all the inner city boroughs, integrating real-time pollution data with environmental covariates: traffic volumes, road proximity, green space coverage, building density, and deprivation indices. This aims to reveal not just what pollution levels are, but why they vary from school to school.

The platform combines a tiered pollution data approach (Breathe London sensors, LAQN reference monitors, and LAEI modelled data) with spatial statistical modelling to produce reliable estimates even where direct sensor coverage is sparse. The planned progression from descriptive analysis through to regression kriging and temporal forecasting will enable the platform to identify pollution patterns during school drop-off and pick-up times, explore correlations between deprivation and pollution exposure, where these patterns invert, and ultimately support evidence-based advocacy for cleaner air at school gates.

A core research thread examines the environmental justice dimension: whether children in more deprived areas face disproportionate pollution exposure, and where the exceptions to that pattern are equally revealing.

The platform is built with Django and PostgreSQL, with Leaflet for interactive mapping. Spatial analysis will be developed using GeoPandas, PySAL, and PyKrige, drawing on freely available open data from the DfT, GLA, Ordnance Survey, and the English Indices of Deprivation. Both the Breathe London sensor network and the London Air Quality Network are managed by the Environmental Research Group at Imperial College London.

## Development Phases

The following roadmap outlines the planned evolution of the platform from its current Lambeth and Southwark focus into a broader research-grade tool.

## Phase 1 — Expand the Foundation

Scale to all inner city London boroughs. Load schools and early-years settings, map them to existing LAEI data, and extend Breathe London and LAQN sensor coverage where available. This is the base layer everything else depends on.

## Phase 2 — Enrich the Data Layer

- Integrate Income/IDACI deprivation data at LSOA level and link to school locations
- Integrate environmental covariate data (traffic volumes, road proximity, green space coverage — see Data Sources below)
- Add historical pollution data to enable trend analysis
- Build ranking and filtering views — worst-polluted schools by borough, sortable and filterable
- Develop deprivation-pollution correlation analysis to explore environmental justice questions

## Phase 3 — Spatial Modelling

- Implement variogram analysis and spatial autocorrelation assessment
- Develop ordinary kriging for spatial interpolation of pollution between sensor locations
- Progress to regression kriging using environmental covariates (traffic density, road proximity, green space, building density, deprivation) to produce modelled pollution surfaces
- Use kriging uncertainty estimates to improve data quality communication to users

## Phase 4 — Temporal Analysis & Forecasting

- Analyse time-of-day pollution patterns using sensor data — morning drop-off, afternoon pick-up, overnight baseline
- Explore time-series and ML approaches for short-term pollution spike forecasting
- Dependent on temporal resolution of sensor coverage achieved in Phase 1

## Phase 5 — Research & Communication Layer

- Build out health impacts content section focused on children
- Publish deprivation-pollution correlation findings with proper statistical treatment
- Frame the platform as a living piece of research with civic and policy value

---

## Data Sources

### Age groups and coverage

"Early years" in England is defined by the Early Years Foundation Stage (EYFS):
birth to the 31 August following a child's fifth birthday. This platform
distinguishes four nested populations within and beyond that range:

| Layer | Ages | Where they are | Data source |
|---|---|---|---|
| Pre-nursery | 0–3 | PVI nurseries, childminders, a few schools admitting at 2–3 | Ofsted EYR, GIAS |
| Nursery | 3–4 | School nursery classes, PVI settings | GIAS (`has_pre_reception_provision`), Ofsted EYR |
| Reception | 4–5 (EYFS) | All primary schools | GIAS |
| Compulsory school age | 5+ | All schools | GIAS |

Notes:
- The GIAS-derived flag `has_pre_reception_provision` marks schools with
  provision *below* reception age (nursery classes, or statutory low age ≤ 3).
  It deliberately excludes reception-only primaries: every primary school has
  EYFS children in reception, so those schools are covered as schools rather
  than flagged.
- The Ofsted slice covers providers on the Early Years Register (0–5). The
  register does not record which ages within 0–5 a provider serves, so it
  cannot distinguish under-3 provision from preschool-only settings.
- Home-based providers (childminders and child care on domestic premises) have addresses and
  postcodes withheld by Ofsted, so they cannot be mapped. They are retained in the data for counts and aggregate analysis. 

### Establishments (Schools & Early-Years Settings)

| Data | Source | Coverage | Access |
|------|--------|----------|--------|
| Schools (all phases) | Get Information about Schools (GIAS), DfE | All state and independent schools; updated daily | get-information-schools.service.gov.uk |
| Early-years childcare providers | Ofsted childcare providers and inspections | All Ofsted-registered providers; published ~3×/year | gov.uk (ODS, provider-level) |

Across Southwark and Lambeth: 213 open schools, of which 125 have pre-reception provision (GIAS extract, September 2026); 283 mappable group settings and 344 home-based providers (Ofsted release as at 31 March 2026).

### Pollution Data (Current Platform)

| Tier | Source | Provider | Resolution | Access |
|------|--------|----------|------------|--------|
| 1 | Breathe London Sensors | Imperial College London ERG | Hourly, point locations | Breathe London API |
| 2 | London Air Quality Network (LAQN) | Imperial College London ERG | 15-min, reference stations | londonair.org.uk API |
| 3 | London Atmospheric Emissions Inventory (LAEI) | Greater London Authority | 20m grid, annual modelled | data.london.gov.uk |

Both the LAQN and Breathe London networks are managed by the Environmental Research Group (ERG) at Imperial College London. Breathe London sensors are co-located at LAQN reference sites and cross-checked against reference data in real-time.

### Environmental Covariates (Planned)

| Factor | Source | Geography | Access |
|--------|--------|-----------|--------|
| Traffic volume (AADF) | DfT Road Traffic Statistics | Road links with lat/lng | Open API (roadtraffic.dft.gov.uk) |
| Green cover | GLA Green and Blue Cover | London-wide shapefile | data.london.gov.uk |
| Green space | OS Open Greenspace | GB points/polygons | osdatahub.os.uk (free) |
| Deprivation (IMD) | English Indices of Deprivation 2025 | LSOA (2021 boundaries, ~1,500 residents) | gov.uk / data.london.gov.uk |
| Child deprivation (IDACI) | IMD sub-domain | LSOA | gov.uk |
| Building density | OS Open Map Local | Building footprints | osdatahub.os.uk (free) |

### Derived Variables Per Establishment

For each school and early years setting, the following environmental variables will be calculated via spatial joins:

- Distance to nearest major road (metres)
- Annual Average Daily Flow on nearest major road (total and by vehicle type)
- Percentage green cover within 200m radius
- Distance to nearest green space
- IMD decile (overall and London-rebased)
- IDACI score (child-specific deprivation)
- Building density within 200m radius

These variables contextualise pollution readings for users, provide covariates for spatial modelling, and enable the deprivation-pollution correlation analysis.

---

## Environmental Justice

A core research thread running through the platform is the analysis of potential correlations between areas of deprivation and school-level pollution exposure, which manifests across the development phases.  The analysis uses the Income domain and IDACI rather than the overall IMD, because the overall index incorporates air quality within its Living Environment section so a correlation is partly baked in rather than revealing a real-world relationship.

- **Phase 2 (Descriptive):** Overlay Income domain and IDACI deprivation data with school pollution levels, showing where the pattern holds and where it breaks down
- **Phase 3 (Analytical):** Deprivation as a covariate in regression kriging spatial models
- **Phase 5 (Research output):** Publishable findings with proper statistical treatment — the exceptions (wealthy areas with high pollution, deprived areas with lower pollution) are as analytically interesting as the correlation itself

---

## Learning Resources

The spatial modelling work draws on the following key resources:

- **Geographic Data Science with Python** (Rey, Arribas-Bel & Wolf) — spatial data, spatial autocorrelation, spatial regression. Free online at geographicdata.science
- **Applied Geostatistics in Python** (Michael Pyrcz / GeostatsGuy) — variograms, kriging, spatial estimation. Free e-book at geostatsguy.github.io/GeostatsPyDemos_Book
- **PyKrige** — Python kriging toolkit supporting ordinary and regression kriging. pykrige.readthedocs.io
- **PySAL** — Python Spatial Analysis Library for spatial statistics and econometrics. pysal.org

---

## Tech Stack

- **Backend:** Django, Python, PostgreSQL, PostGIS
- **Frontend:** HTML, CSS, JavaScript, Leaflet (mapping)
- **Deployment:** Linode VPS (migration from Heroku in progress)
- **Data Processing:** Pandas, GeoPandas (planned)
- **Spatial Analysis:** PyKrige, PySAL (planned)

