import streamlit as st
from musictagger.core import BASEPATH, MP3Table

MAX_DIR_LEVEL = 10


def update_based_on_previous_value(songs: MP3Table, category: str, options=None) -> None:
    if options:
        selection = st.sidebar.selectbox(f'Update {category}',
                                         options=songs.get_entries(category) + ['Select from Options',
                                                                                'Update Manually'])
    else:
        selection = st.sidebar.selectbox(f'Update {category}',
                                         options=songs.get_entries(category) + ['Update Manually'])
    if selection == "Select from Options":
        songs.data[category] = st.sidebar.selectbox(f'Select {category}', options)
    elif selection == 'Update Manually':
        songs.data[category] = st.sidebar.text_input(f'Provide a new entry for {category}', '')
    else:
        songs.data[category] = selection


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
