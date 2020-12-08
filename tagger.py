import string

import streamlit as st

from musictagger import BASEPATH, find_artists, get_table, delete_comment, delete_url, delete_copyright, \
    retag, find_albums_for_artist, set_track_and_disc_number, get_tags, extract_possible_genres

st.title("Welcome to the Music Tagger")
st.markdown("""## Instructions:
1. Select the Albums you would like to retag.
2. Select the procedures to apply from the sidebar.
3. Check the results.
4. If you are happy with the results, press Save.""")

artists = find_artists()

starts_with = st.selectbox('Starting letter', list(string.ascii_uppercase))

artist = st.selectbox("Select Artist", ["None"] + [a for a in find_artists() if str(a).upper().startswith(starts_with)])

album = st.selectbox("Select Album", ["None", "Any"] + [a for a in find_albums_for_artist(artist)])

if artist != "None" and album != "None":
    # make table
    if album == "Any":
        df = get_table(BASEPATH / artist)
    else:
        df = get_table(BASEPATH/artist/album)

    st.write("Old Tags:")
    st.write(df)

    delete_comment_box = st.sidebar.checkbox('Delete Comments')
    if delete_comment_box:
        delete_comment(df)

    delete_url_box = st.sidebar.checkbox('Delete URL')
    if delete_url_box:
        delete_url(df)

    delete_copyright_box = st.sidebar.checkbox('Delete Copyright')
    if delete_copyright_box:
        delete_copyright(df)

    renumber_tracks_box = st.sidebar.checkbox('Update Tracks and Disc numbers')
    if renumber_tracks_box:
        set_track_and_disc_number(df)

    update_genre_box = st.sidebar.checkbox("Update Genre")
    if update_genre_box:
        new_genre_selection = st.sidebar.selectbox('Update Genre', options=extract_possible_genres(df) + ['Other'])
        if new_genre_selection == 'Other':
            new_genre = st.sidebar.text_input('Provide the name for the new Genre', '')
        else:
            new_genre = new_genre_selection
        df['genre'] = new_genre

    st.write("New Tags:")
    st.write(df)

    save_button = st.button("Save")
    if save_button:
        tags = get_tags(df)
        retag(tags)
        st.balloons()