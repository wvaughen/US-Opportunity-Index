import pandas as pd
import geopandas as gpd
import numpy as np
import streamlit as st

import plotly.express as px

import time

# run python -m streamlit run acs_explorer.py to start the streamlit app


# year selection dropdown
selected_year = st.sidebar.selectbox(
    "ACS Data Year",
    options=[2024, 2023, 2022, 2021, 2020],
    index=0,  # defaults to 2024
)


# setting up the metric weight sliders in the sidebar
SLIDERS = ["Income", "Education Attainment", "Unemployment", "Health Insurance Coverage", "Housing Cost Burden"]

DESCRIPTIONS = {
    "Income": "Median household income for the district, normalized relative to the national range. Higher scores indicate greater income.",
    "Education Attainment": "Share of adults with a bachelor's degree or higher. Higher scores indicate more educational attainment.",
    "Unemployment": "Share of the labor force that is unemployed. Higher scores indicate lower unemployment.",
    "Health Insurance Coverage": "Share of residents with health insurance coverage. Higher scores indicate greater coverage.",
    "Housing Cost Burden": "Share of households spending less than 30% of income on housing. Higher scores indicate lower cost burden.",
}

def normalize(changed_key):
    """Rescale all other sliders proportionally so total stays 100."""
    changed_val = st.session_state[changed_key]
    others = {k: st.session_state[k] for k in SLIDERS if k != changed_key}
    others_sum = sum(others.values())
    remaining = 100 - changed_val

    if others_sum == 0:
        # Distribute evenly if all others are zero
        per_slider = remaining / len(others)
        for k in others:
            st.session_state[k] = per_slider
    else:
        # Scale others proportionally
        for k, v in others.items():
            st.session_state[k] = round(v / others_sum * remaining, 2)

# Initialize session state
for key in SLIDERS:
    if key not in st.session_state:
        st.session_state[key] = 20.0  # Start at equal shares (5 × 20 = 100)

st.sidebar.title("Opportunity Index Weight Sliders")

for key in SLIDERS:
    st.sidebar.slider(
        label=f"{key}",
        min_value=0.0,
        max_value=100.0,
        key=key,
        on_change=normalize,
        args=(key,),
    )
    with st.sidebar.expander("About this metric"):
        st.caption(DESCRIPTIONS[key])

total = sum(st.session_state[k] for k in SLIDERS)
st.sidebar.metric("Total", f"{total:.2f}")




# loading the data and caching it to avoid reloading on every interaction
@st.cache_data
def load_data(year):
    return gpd.read_parquet(f"Processed ACS Data/withGeo/acs_{year}_with_geometries.parquet")

df = load_data(selected_year)




# loading the geojson and caching it to avoid reloading on every interaction
@st.cache_data
def get_geojson(_gdf):
    return _gdf.geometry.__geo_interface__  # cache the serialized GeoJSON separately

geojson = get_geojson(df)


# updating the map based on the slider values
COLUMN_MAP = {
    "Income": "income",
    "Education Attainment": "educational attainment",
    "Unemployment": "unemployment",
    "Health Insurance Coverage": "health insurance coverage",
    "Housing Cost Burden": "housing cost burden",
}

def compute_weighted_score(row):
    score = 0
    for slider_name, column_name in COLUMN_MAP.items():
        weight = st.session_state[slider_name] / 100  # Convert percentage to decimal
        score += row[column_name] * weight
    return score

df['weighted_score'] = df.apply(compute_weighted_score, axis=1)
df['score_vs_average'] = df['weighted_score'] - df['weighted_score'].mean()
df['label'] = df['state_name'] + " District " + df['congressional district'] 


@st.fragment
def render_map():
    fig = px.choropleth(
    df.drop(columns="geometry"),  # pass lightweight DataFrame
    geojson=geojson,
    locations=df.index,
    hover_name='label',
    hover_data={
        'population': ":,",
        'weighted_score': ":.2f", 
        'score_vs_average': ":.2f"
        },
    color='score_vs_average',
    color_continuous_scale=[
        (0.0, "red"),
        (0.5, "lightyellow"),  # midpoint = average
        (1.0, "green")],
    color_continuous_midpoint=0,
    title="Opportunity Index by Congressional District (vs. Average)"
    )


    fig.update_geos(visible=True, 
                    scope='usa',
                    projection_type="albers usa",
                    showland=True,
                    landcolor="lightgray",
                    showcoastlines=True,
                    coastlinecolor="black",
                    showlakes=True,
                    lakecolor="lightblue",
                    showocean=True,
                    oceancolor="red",
                    )
    fig.update_layout(
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        coloraxis_colorbar=dict(
            title="vs. Average",
            tickformat=".2f",
        ),
        geo=dict(
            showframe=False,
            showcoastlines=False,
        ),
        dragmode=False 
        )

    fig.update_traces(marker_opacity=0.8)
   
     # --- Display in Streamlit ---
    selected = st.plotly_chart(
        fig,
        use_container_width=True,
        on_select="rerun",  # reruns the app when a district is clicked
        selection_mode="points",
    )

    # Check if a district was clicked
    if selected and selected.selection.points:
        point = selected.selection.points[0]
        district_idx = point["point_index"]
        district_row = df.iloc[district_idx]
        district_label = df["label"].iloc[district_idx]

        # Build a dataframe for the bar chart
        score_cols = list(COLUMN_MAP.values())
        bar_df = pd.DataFrame({
            "Category": list(COLUMN_MAP.keys()),
            "Score": [district_row[col] for col in score_cols],
        })

        st.subheader(f"{district_label}")
        fig_bar = px.bar(
            bar_df,
            x="Category",
            y="Score",
            range_y=[0, 1],
            color="Score",
            color_continuous_scale=["red", "lightyellow", "green"],
            color_continuous_midpoint=0.5,
            title=f"Category Scores",
            labels={"Score": "Score (0–1)"},
        )
        fig_bar.update_layout(
            coloraxis_showscale=False,
            margin={"r": 0, "t": 40, "l": 0, "b": 0},
        )
        st.plotly_chart(fig_bar, use_container_width=True)

render_map()  # only reruns when explicitly invalidated



# Description
st.write("""
    ### About the Opportunity Index
    The Opportunity Index is a composite measure that evaluates the overall opportunity available to residents in each congressional district. It takes into account five key metrics: Income, Education Attainment, Unemployment, Health Insurance Coverage, and Housing Cost Burden. Each metric can be weighted according to user preference using the sliders in the sidebar. The resulting score reflects how each district compares to the national average, with positive values indicating above-average opportunity and negative values indicating below-average opportunity.
""")


# Footer
st.markdown(
    f"""
    <hr style="margin-top: 2rem; border: none; border-top: 1px solid #e0e0e0;">
    <p style="text-align: center; color: gray; font-size: 0.8rem;">
        Data sourced from the 
        <a href="https://www.census.gov/programs-surveys/acs" target="_blank">
            U.S. Census Bureau's American Community Survey (ACS)
        </a>, 5-Year Estimates ({selected_year}).
    </p>
    """,
    unsafe_allow_html=True,
)


