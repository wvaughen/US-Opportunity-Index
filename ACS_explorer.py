import pandas as pd
import numpy as np
import streamlit as st

import time

# run python -m streamlit run acs_explorer.py to start the streamlit app


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

st.sidebar.title("Normalized Sliders")

for key in SLIDERS:
    st.sidebar.slider(
        label=f"Slider {key}",
        min_value=0.0,
        max_value=100.0,
        key=key,
        on_change=normalize,
        args=(key,),
    )

total = sum(st.session_state[k] for k in SLIDERS)
st.sidebar.metric("Total", f"{total:.2f}")




