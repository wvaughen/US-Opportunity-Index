# U.S. Opportunity Index Explorer

An interactive web app for exploring socioeconomic opportunity across all U.S. congressional districts using data from the American Community Survey (ACS). Users can define what "opportunity" means to them by adjusting the weight of five key indicators in real time, generating a customized composite score for every district in the country.

🔗 **[Live App](#)** ← *replace with your Streamlit Community Cloud URL*

![App Screenshot](#) ← *replace with a screenshot after deployment*

---

## What It Does

Most opportunity or quality-of-life indices use fixed, predetermined weights — this app puts that decision in the user's hands. A policy researcher might weight health insurance coverage most heavily; an economist might prioritize income and unemployment. By adjusting five sliders in the sidebar, users generate their own version of the index and see the map update in real time.

**Core features:**
- Interactive choropleth map of all U.S. congressional districts colored by composite opportunity score relative to the national average
- Five adjustable weight sliders — weights auto-normalize to always sum to 100%, no manual math required
- District detail view — click any district on the map to see a breakdown of its individual indicator scores vs. the national average
- Year selector supporting ACS 5-Year Estimates from 2020 through 2024
- State-level filter for zooming into a specific region

---

## Indicators

Each indicator is drawn from ACS 5-Year Subject Tables and normalized to a 0–1 scale using min-max scaling across all districts. For unemployment and housing cost burden, scores are inverted so that a higher score always indicates a better outcome.

| Indicator | ACS Variable | Direction |
|---|---|---|
| Median Household Income | S2506_C01_024E | Higher = Better |
| Bachelor's Degree Attainment Rate | S0102_C01_037E | Higher = Better |
| Unemployment Rate | S2101_C01_034E | Lower = Better ↓ |
| Health Insurance Coverage Rate | S2701_C01_001E | Higher = Better |
| Housing Cost Burden (% spending <30% of income on housing) | S2503_C01_028E | Lower = Better ↓ |

---

## Methodology

**Data Collection:** ACS 5-Year Estimates were pulled via the Census Bureau REST API for all congressional districts across five years (2020–2024). Raw data was saved as CSV files for reproducibility.

**Normalization:** Each indicator was normalized to a 0–1 scale using scikit-learn's `MinMaxScaler`, applied independently per year to account for year-over-year distributional shifts. Unemployment and housing cost burden were inverted (`1 - score`) so that higher values consistently indicate better conditions across all indicators.

**Composite Scoring:** The weighted composite score is calculated as:

```
composite_score = Σ (indicator_score × user_weight)
```

where user-defined weights are normalized to sum to 1.0. The displayed map value is each district's score relative to the national average (`score - mean(score)`), making it easy to identify above- and below-average districts regardless of the chosen weights.

**Geospatial Data:** Congressional district boundaries were sourced from the U.S. Census Bureau TIGER/Line Shapefiles (118th Congress). Boundaries were simplified using a tolerance of 0.01 degrees to reduce file size while preserving topology, then merged with ACS data on GEOID (state FIPS + district code) and stored as GeoParquet files for fast loading.

---

## Tech Stack

- **Data Collection:** Python (`requests`, Census REST API)
- **Data Processing:** Python (`pandas`, `numpy`, `scikit-learn`, `geopandas`)
- **App:** Streamlit
- **Visualization:** Plotly Express (choropleth map, bar charts)
- **Geospatial:** GeoPandas, Census TIGER/Line Shapefiles
- **Storage:** GeoParquet (via `pyarrow`) for efficient geospatial data loading

---

## Project Structure

```
us-opportunity-index/
│
├── ACS_data_prep.ipynb        # Data collection, normalization, and geospatial merging
├── ACS_explorer.py            # Streamlit app
├── requirements.txt
│
├── Raw ACS Data/              # Raw CSVs from Census API (one per year)
├── Processed ACS Data/
│   └── withGeo/               # GeoParquet files with district boundaries merged
└── Shapefiles/                # Census TIGER/Line shapefiles by state
```

---

## Running Locally

**1. Clone the repo**
```bash
git clone https://github.com/yourusername/us-opportunity-index.git
cd us-opportunity-index
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Add your Census API key**

Request a free key at [api.census.gov/data/key_signup.html](https://api.census.gov/data/key_signup.html) and add it to `ACS_data_prep.ipynb`.

**4. Run the data prep notebook**

Run `ACS_data_prep.ipynb` end-to-end to pull ACS data, process it, and generate the GeoParquet files the app depends on.

**5. Launch the app**
```bash
python -m streamlit run ACS_explorer.py
```

---

## Data Sources

- [U.S. Census Bureau — American Community Survey 5-Year Estimates](https://www.census.gov/programs-surveys/acs), 2020–2024
- [U.S. Census Bureau — TIGER/Line Shapefiles, 118th Congressional Districts](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html)

---

## About

Built as a portfolio project to demonstrate applied data skills in API integration, geospatial analysis, data normalization, and interactive visualization. The methodology draws on experience designing composite indices and analysis frameworks for federal policy research.
