<image-src="https://github.com/walkenho/mp3-tagger/blob/main/cover.png">

# MP3-Tagger

An app to help organize MP3 tags by providing an intuitive interface to bulk-analyze and retag MP3 files.

Written in python using the streamlit interface and dockerized for ease of use.

In addition to the retagging functionality also provides the option to produce analytics on the file tag health.
(Note that the analytics functionality can currently on be used locally, not as part of the docker functionality.)

Usage (docker-based):
* Build the docker image 
* Run the image using `docker run -p 8501:8501 -v full-path-to-your-local-music-directory:/home/data/ docker-image-name`.

Follow the instructions provided at the top of the app. 

Happy Organizing! :) 
