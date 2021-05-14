import string
import pandas as pd

import streamlit as st

from musictagger import BASEPATH, find_artists_for_category, get_table, delete_column, \
    retag, find_albums_for_category_and_artist, get_tags, extract_options, \
    DISCNUMBER, ALBUM, GENRE, ARTIST, ALBUMARTIST, ENCODEDBY, COPYRIGHT, set_combined_track_number, \
    set_combined_disc_number, TITLE, DATE, \
    TRACKNUMBER, find_categories, LANGUAGE, add_albumart, LENGTH, BASEPATH

MAX_DIR_LEVEL = 10


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



def get_albumpath():
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

folder = get_albumpath()
if folder:
#
#
#category = st.selectbox("Select Category", ["None", "Any"] + list(find_categories()))
#
#possible_starting_letters = sorted(set([str(artist)[0].upper() for artist in find_artists_for_category(category)]))
#
#starts_with = st.selectbox('Starting letter',  possible_starting_letters + ['Any'])
#
#if starts_with != 'Any':
#    artist = st.selectbox("Select Artist", ["None", "Any"]
#                      + [a for a in find_artists_for_category(category) if str(a).upper().startswith(starts_with)])
#else:
#    artist = st.selectbox("Select Artist", ["None", "Any"]
#                          + [a for a in find_artists_for_category(category)])
#
#if artist == "Any":
#    album_options = ["Any"]
#else:
#    album_options = ["None", "Any"] + [a for a in find_albums_for_category_and_artist(category, artist)]
#
#album = st.selectbox("Select Album", album_options)
#
#if album != "None":
#    # make table
#    if artist == "Any":
#        folder = BASEPATH
#    elif album == "Any":
#        folder = BASEPATH / category / artist
#    else:
#        folder = BASEPATH / category / artist / album
    df = get_table(folder)

    st.header('Health Check')
    st.subheader('Inconsistencies')
    #TODO: Implement check for nans
    problem_counter = 0
    missing_tags = []
    for category in [ALBUM, ARTIST, ALBUMARTIST, GENRE, LANGUAGE, DATE]:
        if category in df.columns:
            values = df[category].unique()
            if len(values) > 1:
                try:
                    st.warning(f"{category}: Multiple Entries found [{(', ').join(values)}]")
                except TypeError:
                    values = [str(v) for v in values]
                    st.warning(f"{category}: Multiple Entries found [{(', ').join(values)}]")
                problem_counter = problem_counter + 1
        else:
            missing_tags.append(category)

    for category in df.columns:
        if df[category].isnull().values.any():
            st.warning(f"{category}: Contains Nulls - filling with empty string")
            df[category].fillna('', inplace=True)


    if problem_counter == 0:
        st.success(f"No inconsistencies detected")

    st.subheader('Missing Tags')
    if len(missing_tags) > 0:
        for category in missing_tags:
            st.warning(f"{category}: Tags not found")
    else:
        st.success(f"No missing tags detected")

    st.markdown("### Original Tags:")
    st.write(df)

    if st.sidebar.checkbox(f"Update {ALBUM}"):
        update_based_on_previous_value(df, ALBUM)

    if st.sidebar.checkbox(f"Update {ARTIST}"):
        update_based_on_previous_value(df, ARTIST)

    if st.sidebar.checkbox(f"Update {ALBUMARTIST}"):
        update_based_on_previous_value(df, ALBUMARTIST)

    if st.sidebar.checkbox(f"Set {ALBUMARTIST} to {ARTIST}"):
        df[ALBUMARTIST] = df[ARTIST]

    if st.sidebar.checkbox(f"Update {GENRE}"):
        update_based_on_previous_value(df, GENRE)

    if st.sidebar.checkbox(f"Set {LANGUAGE} to ..."):
        language = st.sidebar.selectbox("Set Language to:", ['english', 'spanish', 'deutsch', 'french'])
        df[LANGUAGE] = language

    if st.sidebar.checkbox(f"Update {LANGUAGE}"):
        update_based_on_previous_value(df, LANGUAGE)

    if st.sidebar.checkbox(f'Update {DATE}'):
        update_based_on_previous_value(df, DATE)

    if st.sidebar.checkbox(f'Set {TITLE}'):
        title = st.sidebar.text_input(f"Set {TITLE}")
        df[TITLE] = title

    if st.sidebar.checkbox(f'Set {TRACKNUMBER}'):
        tracknumber = st.sidebar.text_input(f"Set {TRACKNUMBER}")
        df[TRACKNUMBER] = tracknumber

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

    if st.sidebar.checkbox(f'Delete {LENGTH}'):
        delete_column(df, LENGTH)

    if st.sidebar.checkbox(f'Update bpm'):
        update_based_on_previous_value(df, 'bpm')

    if st.sidebar.checkbox(f'Update media'):
        update_based_on_previous_value(df, 'media')

    if st.sidebar.checkbox(f'Update organization'):
        update_based_on_previous_value(df, 'organization')


    st.markdown("### Updated Tags:")
    st.write(df)

    save_button = st.button("Save")
    if save_button:
        tags = get_tags(df)
        retag(tags)
        st.balloons()

    st.header('CoverArt')
    if st.checkbox(f'Add Coverart'):
        jpgs = ([p.relative_to(BASEPATH) for p in folder.glob("*.jpg")]
                 + [p.relative_to(BASEPATH) for p in folder.glob("*.jpeg")])
        image_path = st.selectbox('Choose Image File',
                                  options=jpgs)

        save_button_coverart = st.button("Save Coverart")
        if save_button_coverart:
            if image_path:
                for audio_path in df['filename']:
                    add_albumart(BASEPATH/audio_path, BASEPATH/image_path)
                st.balloons()
            else:
                st.error("Please specify filepath to coverart")
