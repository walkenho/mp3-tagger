import streamlit as st

from mp3tagger.core import MP3Table, set_mp3_coverart, TagNames, BASEPATH
from mp3tagger.interface import get_albumpath_from_interface, update_based_on_previous_value

st.title("Welcome to the MP3 Tagger")
st.markdown("""## Instructions:
1. Select the Albums you would like to retag. - Drill down as many layers as needed.
 Choose "All" to load all MP3s in the selected folder (including subfolders).
2. Select the cleaning steps to apply from the sidebar. 
3. The proposed new tags are shown in the bottom table. Check the results.
4. Once you are happy with the results, press Save.
5. If desired, add a cover image to your files. You can choose from jpegs/jpgs in the current folder. If your
image does not appear, check the file extension. 
""")

folder = get_albumpath_from_interface()
if folder:
    mp3table = MP3Table(folder)
    mp3table.load()

    st.header('Health Check')
    problem_counter = 0
    missing_tags = []
    for category in [TagNames.ALBUM.value, TagNames.ARTIST.value, TagNames.ALBUMARTIST.value,
                     TagNames.GENRE.value, TagNames.LANGUAGE.value, TagNames.DATE.value]:
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
    major_update_categories = [TagNames.ALBUM.value, TagNames.ARTIST.value, TagNames.ALBUMARTIST.value,
                               TagNames.GENRE.value, TagNames.LANGUAGE.value, TagNames.DATE.value]
    for category in major_update_categories:
        if category == TagNames.LANGUAGE.value:
            options = ['english', 'spanish', 'deutsch', 'french']
        else:
            options = None
        if st.sidebar.checkbox(f'Update {category}'):
            update_based_on_previous_value(mp3table, category, options)

        if category == TagNames.ALBUMARTIST.value:
            if st.sidebar.checkbox(f"Set {TagNames.ALBUMARTIST.value} to {TagNames.ARTIST.value}"):
                mp3table.data[TagNames.ALBUMARTIST.value] = mp3table.data[TagNames.ARTIST.value]

    if st.sidebar.checkbox(f'Cast {TagNames.TRACKNUMBER.value} to n/m format'):
        mp3table.set_combined_track_number()

    if st.sidebar.checkbox(f"Set {TagNames.DISCNUMBER.value}"):
        disc_number = st.sidebar.text_input(f"Set {TagNames.DISCNUMBER.value}")
        mp3table.data[TagNames.DISCNUMBER.value] = disc_number

    if st.sidebar.checkbox(f'Cast {TagNames.DISCNUMBER.value} to n/m format'):
        mp3table.set_combined_disc_number()

    st.sidebar.markdown("### Popular - Single Track")
    if st.sidebar.checkbox(f'Set {TagNames.TITLE.value}'):
        mp3table.data[TagNames.TITLE.value] = st.sidebar.text_input(f"Set {TagNames.TITLE.value}")

    if st.sidebar.checkbox(f'Set {TagNames.TRACKNUMBER.value}'):
        mp3table.data[TagNames.TRACKNUMBER.value] = st.sidebar.text_input(f"Set {TagNames.TRACKNUMBER.value}")

    st.sidebar.markdown("### Delete Tags")
    tags_to_delete = st.sidebar.multiselect('Tags to delete (multi-choice)',
                                            options=list(set(mp3table.data.columns).difference(['filename'])))
    for category in tags_to_delete:
        mp3table.delete_tag(category)

    minor_categories = set(mp3table.data.columns)\
            .difference(major_update_categories)\
            .difference(['filename', TagNames.TRACKNUMBER.value, TagNames.DISCNUMBER.value, TagNames.TITLE.value])
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