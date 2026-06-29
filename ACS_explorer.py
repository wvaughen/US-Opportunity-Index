import pandas as pd
import geopandas as gpd
import numpy as np
import streamlit as st

import plotly.express as px

import time

# run python -m streamlit run acs_explorer.py to start the streamlit app

# setting up the metric weight sliders in the sidebar
SLIDERS = ["Income", "Education Attainment", "Unemployment", "Health Insurance Coverage", "Housing Cost Burden"]

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

total = sum(st.session_state[k] for k in SLIDERS)
st.sidebar.metric("Total", f"{total:.2f}")




# loading the data and caching it to avoid reloading on every interaction
@st.cache_data
def load_data():
    return gpd.read_parquet("Processed ACS Data/Shapefiles/2024/acs_2024_with_geometries.parquet")

df = load_data()



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
    st.plotly_chart(fig)

render_map()  # only reruns when explicitly invalidated


st.write("""
    ### About the Opportunity Index
    The Opportunity Index is a composite measure that evaluates the overall opportunity available to residents in each congressional district. It takes into account five key metrics: Income, Education Attainment, Unemployment, Health Insurance Coverage, and Housing Cost Burden. Each metric can be weighted according to user preference using the sliders in the sidebar. The resulting score reflects how each district compares to the national average, with positive values indicating above-average opportunity and negative values indicating below-average opportunity.
""")





