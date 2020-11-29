import string

import streamlit as st

from musictagger import BASEPATH, find_artists, get_table, delete_comment, delete_url, delete_copyright, \
    get_tags_from_v2, retag, find_albums_for_artist

st.title("Welcome to the Music Tagger")

artists = find_artists()

starts_with = st.selectbox('Starting letter', list(string.ascii_uppercase))

artist = st.selectbox("Select Artist", ["None"] + [a for a in find_artists() if str(a).upper().startswith(starts_with)])

album = st.selectbox("Select Album", ["None", "Any"] + [a for a in find_albums_for_artist(artist)])

if artist != "None" and album != "None":
    # make table
    if album == "Any":
        df = get_table(BASEPATH / artist, 'v2')
    else:
        df = get_table(BASEPATH/artist/album, 'v2')

    st.write("Old Tags:")
    st.write(df)

    delete_comment_box = st.checkbox('Delete Comments')
    if delete_comment_box:
        delete_comment(df)

    delete_url_box = st.checkbox('Delete URL')
    if delete_url_box:
        delete_url(df)

    delete_copyright_box = st.checkbox('Delete Copyright')
    if delete_copyright_box:
        delete_copyright(df)

    st.write("New Tags:")
    st.write(df)

    save_button = st.button("Save")
    if save_button:
        tags = get_tags_from_v2(df)
        #retag(tags)
        st.balloons()