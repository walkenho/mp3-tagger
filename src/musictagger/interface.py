import pandas as pd
import streamlit as st
from musictagger.core import BASEPATH, extract_options

MAX_DIR_LEVEL = 10


def update_based_on_previous_value(df: pd.DataFrame, column: str, options=None) -> None:
    if options:
        selection = st.sidebar.selectbox(f'Update {column}',
                                         options=extract_options(df, column) + ['Select from Options',
                                                                                'Update Manually'])
    else:
        selection = st.sidebar.selectbox(f'Update {column}',
                                         options=extract_options(df, column) + ['Update Manually'])
    if selection == "Select from Options":
        df[column] = st.sidebar.selectbox(f'Select {column}', options)
    elif selection == 'Update Manually':
        df[column] = st.sidebar.text_input(f'Provide a new entry for {column}', '')
    else:
        df[column] = selection


def get_albumpath_from_interface():
    current_path = BASEPATH
    selection = []
    for ll in range(MAX_DIR_LEVEL):
        options = [entry.relative_to(current_path) for entry in current_path.glob('*')]
        selection.append(st.selectbox("SELECT", ["None", "All"] + options))
        if selection[ll] == "None":
            return None
        elif selection[ll] == "All":
            return current_path
        else:
            current_path = current_path / selection[ll]
