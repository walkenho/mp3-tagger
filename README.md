<image src="https://github.com/walkenho/mp3-tagger/blob/main/cover.png">

# MP3-Tagger

An app to help organize MP3 tags by providing an intuitive interface to bulk-analyze and retag MP3 files.

Written in python it uses mutagen for tagging, streamlit to build the interface and comes dockerized for ease of use.

In addition to the retagging functionality, it provides the option to produce analytics on the file tag health.
(Note that the analytics functionality can currently on be used locally, not as part of the docker functionality.)

Usage (docker-based):
* Build the docker image 
* Run the image using `docker run -p 8501:8501 -v full-path-to-your-local-music-directory:/home/data/ docker-image-name`.

Follow the instructions provided at the top of the app. 

Happy Organizing! :)

PS: The purpose of this app is to make it easy for the user to manually standardize
MP3 tags based on the tags of other MP3s or by manual specification. If you are looking for 
an app that allows tagging based on audio finger prints, there are great, professional,
free-for-use solutions out there (personally, I have made good experiences with Picasa.) 
