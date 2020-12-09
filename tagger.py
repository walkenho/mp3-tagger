import string

import streamlit as st

from musictagger import BASEPATH, find_artists, get_table, delete_column, \
    retag, find_albums_for_artist, set_track_and_disc_number, get_tags, extract_options, \
    DISCNUMBER, ALBUM, GENRE, ARTIST, ENCODEDBY, COPYRIGHT


def update_based_on_previous_value(df, column):
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

starts_with = st.selectbox('Starting letter', list(string.ascii_uppercase))

artist = st.selectbox("Select Artist", ["None"] + [a for a in find_artists() if str(a).upper().startswith(starts_with)])

album = st.selectbox("Select Album", ["None", "All"] + [a for a in find_albums_for_artist(artist)])

if artist != "None" and album != "None":
    # make table
    if album == "All":
        df = get_table(BASEPATH / artist)
    else:
        df = get_table(BASEPATH/artist/album)

    st.markdown("### Original Tags:")
    st.write(df)

    if st.sidebar.checkbox(f"Update {ALBUM}"):
        update_based_on_previous_value(df, ALBUM)

    if st.sidebar.checkbox(f"Update {ARTIST}"):
        update_based_on_previous_value(df, ARTIST)

    if st.sidebar.checkbox(f"Update {GENRE}"):
        update_based_on_previous_value(df, GENRE)

    if st.sidebar.checkbox(f"Set {DISCNUMBER}"):
        disc_number = st.sidebar.text_input(f"Set {DISCNUMBER}")
        df[DISCNUMBER] = disc_number

    if st.sidebar.checkbox('Reformat track numbers and disc numbers'):
        set_track_and_disc_number(df)

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