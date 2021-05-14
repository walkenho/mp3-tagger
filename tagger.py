import string
import pandas as pd

import streamlit as st

from musictagger.core import get_table, delete_column, \
    retag, get_tags, \
    DISCNUMBER, ALBUM, GENRE, ARTIST, ALBUMARTIST, ENCODEDBY, COPYRIGHT, set_combined_track_number, \
    set_combined_disc_number, TITLE, DATE, \
    TRACKNUMBER, LANGUAGE, add_albumart, LENGTH, BASEPATH
from musictagger.interface import get_albumpath_from_interface, update_based_on_previous_value

st.title("Welcome to the Music Tagger")
st.markdown("""## Instructions:
1. Select the Albums you would like to retag.
2. Select the procedures to apply from the sidebar.
3. Check the results.
4. If you are happy with the results, press Save.""")


folder = get_albumpath_from_interface()
if folder:
    tagtable = get_table(folder)

    st.header('Health Check')
    st.subheader('Inconsistencies')
    #TODO: Implement check for nans
    problem_counter = 0
    missing_tags = []
    for category in [ALBUM, ARTIST, ALBUMARTIST, GENRE, LANGUAGE, DATE]:
        if category in tagtable.columns:
            if tagtable[category].isnull().values.any():
                st.warning(f"{category}: Contains Nulls - filling with empty string")
                tagtable[category].fillna('', inplace=True)

            category_values = [str(v) for v in tagtable[category].unique()]
            if len(category_values) > 1:
                st.warning(f"{category}: Multiple Entries found [{(', ').join(category_values)}]")
                problem_counter = problem_counter + 1
        else:
            st.warning(f"{category}: Tags not found")

    if problem_counter == 0:
        st.success(f"No inconsistencies detected")

    st.markdown("### Original Tags:")
    st.write(tagtable)

    # Build sidebar menu
    st.sidebar.markdown("# Cleaning Tools")
    if st.sidebar.checkbox(f"Update {ALBUM}"):
        update_based_on_previous_value(tagtable, ALBUM)

    if st.sidebar.checkbox(f"Update {ARTIST}"):
        update_based_on_previous_value(tagtable, ARTIST)

    if st.sidebar.checkbox(f"Update {ALBUMARTIST}"):
        update_based_on_previous_value(tagtable, ALBUMARTIST)

    if st.sidebar.checkbox(f"Set {ALBUMARTIST} to {ARTIST}"):
        tagtable[ALBUMARTIST] = tagtable[ARTIST]

    if st.sidebar.checkbox(f"Update {GENRE}"):
        update_based_on_previous_value(tagtable, GENRE)

    if st.sidebar.checkbox(f"Set {LANGUAGE} to ..."):
        language = st.sidebar.selectbox("Set Language to:", ['english', 'spanish', 'deutsch', 'french'])
        tagtable[LANGUAGE] = language

    if st.sidebar.checkbox(f"Update {LANGUAGE}"):
        update_based_on_previous_value(tagtable, LANGUAGE)

    if st.sidebar.checkbox(f'Update {DATE}'):
        update_based_on_previous_value(tagtable, DATE)

    if st.sidebar.checkbox(f'Set {TITLE}'):
        title = st.sidebar.text_input(f"Set {TITLE}")
        tagtable[TITLE] = title

    if st.sidebar.checkbox(f'Set {TRACKNUMBER}'):
        tracknumber = st.sidebar.text_input(f"Set {TRACKNUMBER}")
        tagtable[TRACKNUMBER] = tracknumber

    if st.sidebar.checkbox(f'Cast {TRACKNUMBER} to n/m format'):
        set_combined_track_number(tagtable)

    if st.sidebar.checkbox(f"Set {DISCNUMBER}"):
        disc_number = st.sidebar.text_input(f"Set {DISCNUMBER}")
        tagtable[DISCNUMBER] = disc_number

    if st.sidebar.checkbox(f'Cast {DISCNUMBER} to n/m format'):
        set_combined_disc_number(tagtable)

    if st.sidebar.checkbox(f'Delete {ENCODEDBY}'):
        delete_column(tagtable, ENCODEDBY)

    if st.sidebar.checkbox(f'Delete {COPYRIGHT}'):
        delete_column(tagtable, COPYRIGHT)

    if st.sidebar.checkbox(f'Delete {LENGTH}'):
        delete_column(tagtable, LENGTH)

    if st.sidebar.checkbox(f'Update bpm'):
        update_based_on_previous_value(tagtable, 'bpm')

    if st.sidebar.checkbox(f'Update media'):
        update_based_on_previous_value(tagtable, 'media')

    if st.sidebar.checkbox(f'Update organization'):
        update_based_on_previous_value(tagtable, 'organization')


    st.markdown("### Updated Tags:")
    st.write(tagtable)

    save_button = st.button("Save")
    if save_button:
        tags = get_tags(tagtable)
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
                for audio_path in tagtable['filename']:
                    add_albumart(BASEPATH/audio_path, BASEPATH/image_path)
                st.balloons()
            else:
                st.error("Please specify filepath to coverart")
