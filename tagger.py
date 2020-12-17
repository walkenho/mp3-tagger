import string
import pandas as pd

import streamlit as st

from musictagger import BASEPATH, find_artists_for_category, get_table, delete_column, \
    retag, find_albums_for_category_and_artist, get_tags, extract_options, \
    DISCNUMBER, ALBUM, GENRE, ARTIST, ENCODEDBY, COPYRIGHT, set_combined_track_number, set_combined_disc_number, \
    TRACKNUMBER, find_categories


def update_based_on_previous_value(df: pd.DataFrame, column: str) -> None:
    new_selection = st.sidebar.selectbox(f'Update {column}',
                                         options=extract_options(df, column) + ['Update Manually'])
    if new_selection != 'Update Manually':
        df[column] = new_selection
    else:
        df[column] = st.sidebar.text_input(f'Provide a new entry for {column}', '')


st.title("Welcome to the Music Tagger")
st.markdown("""## Instructions:
1. Select the Albums you would like to retag.
2. Select the procedures to apply from the sidebar.
3. Check the results.
4. If you are happy with the results, press Save.""")

st.sidebar.markdown("# Cleaning Tools")
category = st.selectbox("Select Category", ["None", "Any"] + list(find_categories()))

possible_starting_letters = [str(artist)[0].upper() for artist in find_artists_for_category(category)]

starts_with = st.selectbox('Starting letter',  possible_starting_letters + ['Any'])

if starts_with != 'Any':
    artist = st.selectbox("Select Artist", ["None", "Any"]
                      + [a for a in find_artists_for_category(category) if str(a).upper().startswith(starts_with)])
else:
    artist = st.selectbox("Select Artist", ["None", "Any"]
                          + [a for a in find_artists_for_category(category)])

if artist == "Any":
    album_options = ["Any"]
else:
    album_options = ["None", "Any"] + [a for a in find_albums_for_category_and_artist(category, artist)]

album = st.selectbox("Select Album", album_options)

if album != "None":
    # make table
    if artist == "Any":
        df = get_table(BASEPATH)
    elif album == "Any":
        df = get_table(BASEPATH / category / artist)
    else:
        df = get_table(BASEPATH / category / artist / album)

    st.markdown("### Original Tags:")
    st.write(df)

    if st.sidebar.checkbox(f"Update {ALBUM}"):
        update_based_on_previous_value(df, ALBUM)

    if st.sidebar.checkbox(f"Update {ARTIST}"):
        update_based_on_previous_value(df, ARTIST)

    if st.sidebar.checkbox(f"Update {GENRE}"):
        update_based_on_previous_value(df, GENRE)

    if st.sidebar.checkbox(f'Cast {TRACKNUMBER} to n/m format'):
        set_combined_track_number(df)

    if st.sidebar.checkbox(f"Set {DISCNUMBER}"):
        disc_number = st.sidebar.text_input(f"Set {DISCNUMBER}")
        df[DISCNUMBER] = disc_number

    if st.sidebar.checkbox(f'Cast {DISCNUMBER} to n/m format'):
        set_combined_disc_number(df)

    if st.sidebar.checkbox(f'Delete {ENCODEDBY}'):
        delete_column(df, ENCODEDBY)

    if st.sidebar.checkbox(f'Delete {COPYRIGHT}'):
        delete_column(df, COPYRIGHT)

    st.markdown("### Updated Tags:")
    st.write(df)

    save_button = st.button("Save")
    if save_button:
        tags = get_tags(df)
        retag(tags)
        st.balloons()
