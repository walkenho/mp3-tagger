import streamlit as st

from mp3tagger.core import MP3Table, set_mp3_coverart,\
    DISCNUMBER, ALBUM, GENRE, ARTIST, ALBUMARTIST, \
    TITLE, DATE, TRACKNUMBER, LANGUAGE, BASEPATH
from mp3tagger.interface import get_albumpath_from_interface, update_based_on_previous_value

st.title("Welcome to the Music Tagger")
st.markdown("""## Instructions:
1. Select the Albums you would like to retag.
2. Select the procedures to apply from the sidebar.
3. Check the results.
4. If you are happy with the results, press Save.
5. If desired, select a cover image""")

folder = get_albumpath_from_interface()
if folder:
    mp3table = MP3Table(folder)
    mp3table.load()

    st.header('Health Check')
    problem_counter = 0
    missing_tags = []
    for category in [ALBUM, ARTIST, ALBUMARTIST, GENRE, LANGUAGE, DATE]:
        if category in mp3table.data.columns:
            if mp3table.data[category].isnull().values.any():
                st.warning(f"{category}: Contains Nulls")

            category_values = mp3table.data[category].dropna().astype('str').unique()
            if len(category_values) > 1:
                st.warning(f"{category}: Multiple Entries found [{', '.join(category_values)}]")
                problem_counter = problem_counter + 1
        else:
            st.warning(f"{category}: Tags not found")

    if problem_counter == 0:
        st.success(f"No inconsistencies detected")

    st.header("Original Tags")
    st.write(mp3table.data)

    # Build sidebar menu
    st.sidebar.markdown("# Cleaning Tools")
    st.sidebar.markdown("### Popular - Album/Multiple Tracks")
    major_update_categories = [ALBUM, ARTIST, ALBUMARTIST, GENRE, LANGUAGE, DATE]
    for category in major_update_categories:
        if category == LANGUAGE:
            options = ['english', 'spanish', 'deutsch', 'french']
        else:
            options = None
        if st.sidebar.checkbox(f'Update {category}'):
            update_based_on_previous_value(mp3table, category, options)

        if category == ALBUMARTIST:
            if st.sidebar.checkbox(f"Set {ALBUMARTIST} to {ARTIST}"):
                mp3table.data[ALBUMARTIST] = mp3table.data[ARTIST]

    if st.sidebar.checkbox(f'Cast {TRACKNUMBER} to n/m format'):
        mp3table.set_combined_track_number()

    if st.sidebar.checkbox(f"Set {DISCNUMBER}"):
        disc_number = st.sidebar.text_input(f"Set {DISCNUMBER}")
        mp3table.data[DISCNUMBER] = disc_number

    if st.sidebar.checkbox(f'Cast {DISCNUMBER} to n/m format'):
        mp3table.set_combined_disc_number()

    st.sidebar.markdown("### Popular - Single Track")
    if st.sidebar.checkbox(f'Set {TITLE}'):
        mp3table.data[TITLE] = st.sidebar.text_input(f"Set {TITLE}")

    if st.sidebar.checkbox(f'Set {TRACKNUMBER}'):
        mp3table.data[TRACKNUMBER] = st.sidebar.text_input(f"Set {TRACKNUMBER}")

    st.sidebar.markdown("### Delete Tags")
    tags_to_delete = st.sidebar.multiselect('Tags to delete (multi-choice)',
                                            options=list(set(mp3table.data.columns).difference(['filename'])))
    for category in tags_to_delete:
        mp3table.delete_tag(category)

    minor_categories = set(mp3table.data.columns)\
            .difference(major_update_categories)\
            .difference(['filename', TRACKNUMBER, DISCNUMBER, TITLE])
    if minor_categories:
        st.sidebar.markdown("### Other")
        for category in minor_categories:
            if st.sidebar.checkbox(f'Update {category}'):
                update_based_on_previous_value(mp3table, category)

    st.header("Updated Tags")
    st.write(mp3table.data)

    save_button = st.button("Save")
    if save_button:
        mp3table.retag()
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
                for audio_path in mp3table.data['filename']:
                    set_mp3_coverart(audio_path, BASEPATH / image_path)
                st.balloons()
            else:
                st.error("Please specify filepath to coverart")