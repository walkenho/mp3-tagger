import glob
from dataclasses import dataclass
from pathlib import Path

import mutagen
import pandas as pd
from typing import List

from mutagen.asf import ASFError
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError, ID3, APIC
from mutagen.mp3 import HeaderNotFoundError, error, MP3

from datetime import datetime
import json

#BASEPATH = Path('/media/walkenho/Seagate Backup Plus Drive/Eigene Musik')
BASEPATH = Path('/home/walkenho/repositories/music-tagger/Juliane Werding/')

DISCNUMBER = 'discnumber'
ALBUM = 'album'
GENRE = 'genre'
ARTIST = 'artist'
ALBUMARTIST = 'albumartist'
ENCODEDBY = 'encodedby'
COPYRIGHT = 'copyright'
TRACKNUMBER = 'tracknumber'
TITLE = 'title'
DATE = 'date'
LANGUAGE = 'language'
LENGTH = 'length'
COMPOSER= 'composer'


def find_all_mp3s(path):
    return [Path(filename) for filename in
               glob.iglob(str(path / '**' / '*.mp3'), recursive=True)]


@dataclass
class MP3Table:
    path: Path
    data: pd.DataFrame = pd.DataFrame()

    def load(self):
        self.data = pd.DataFrame()
        for f in find_all_mp3s(self.path):
            audio = load_mp3(f)
            if audio:
                if not dict(audio).keys():
                    self.data = self.data.append(pd.DataFrame.from_dict({'filename': [f.relative_to(BASEPATH)]}))
                else:
                    self.data = self.data.append(pd.DataFrame.from_dict({**dict(audio), 'filename': f.relative_to(BASEPATH)}))

    def retag(self):
        for filename, row in self.data.set_index('filename').iterrows():
            tag_song(BASEPATH/filename, **row.to_dict())


def load_mp3(path: Path):
    try:
        audio = EasyID3(path)
        return audio
    except ID3NoHeaderError:
        try:
            audio = mutagen.File(path, easy=True)
            audio.add_tags()
            return audio
        except HeaderNotFoundError:
            print(f"Header Not Found error for file {path} - Not  valid MP3 file")
        except ASFError:
            print(f"ASFError for file {path}")
    except Exception as err:
        if err.args[0] == "Header size not synchsafe":
            print(f"Encountered Header Size not synchsafe error in file {path}")
        else:
            print(f"Undefined error detected {err}")
            raise err


def tag_song(filepath: Path, **attrs) -> None:
    """
    Allowed tags:
    * album
    * artist
    * albumartist
    * date
    * discnumber
    * tracknumber
    * genre
    * language
    * encodedby
    * copyright
    * title
    * length

    * 'bpm', 'compilation',
    'composer', 'lyricist', 'length', 'media', 'mood',
    'version', 'conductor', 'arranger',  'organization',
    'author', 'albumartistsort', 'albumsort', 'composersort', 'artistsort', 'titlesort',
    'isrc', 'discsubtitle', 'originaldate', 'performer:*', 'musicbrainz_trackid',
    'website', 'replaygain_*_gain', 'replaygain_*_peak', 'musicbrainz_artistid', 'musicbrainz_albumid',
    'musicbrainz_albumartistid', 'musicbrainz_trmid', 'musicip_puid', 'musicip_fingerprint',
    'musicbrainz_albumstatus', 'musicbrainz_albumtype', 'releasecountry', 'musicbrainz_discid',
    'asin', 'performer', 'barcode', 'catalognumber', 'musicbrainz_releasetrackid',
     'musicbrainz_releasegroupid', 'musicbrainz_workid', 'acoustid_fingerprint', 'acoustid_id'
    """

    audio = load_mp3(filepath)

    for k, v in attrs.items():
        audio[k] = v

    audio.save()


def delete_column(df: pd.DataFrame, column: str):
    #todo: actually drop tags
    df[column] = ""


def track_number_from_track_total_track_combination(track_string:str) -> int:
    """Extract the numerical tracknumber from a string track number.
     Input can be of format:
    * track
    * track/total tracks
    """
    return int(str(track_string).split('/')[0])


def create_combined_track_nr(track_int: int, artist: str, album: str, disc_int: int, mydict: dict) -> str:
    return f"{track_int:02}/{mydict[(artist, album, disc_int)]}"


def create_combined_disc_nr(disc_int: int, artist: str, album: str, mydict: dict) -> str:
    return f"{disc_int}/{mydict[(artist, album)]}"


def set_combined_track_number(df: pd.DataFrame) -> None:
    if DISCNUMBER not in df.columns:
        df['disc_int'] = 1
    else:
        df[DISCNUMBER] = df[DISCNUMBER].fillna(1)
        df['disc_int'] = df[DISCNUMBER].map(lambda x: track_number_from_track_total_track_combination(x))

    df['track_int'] = df[TRACKNUMBER].map(lambda x: track_number_from_track_total_track_combination(x))

    if 'albumartist' not in df.columns:
        df['albumartist'] = df['artist']
        del_albumartist = True
    else:
        del_albumartist = False

    max_track_dict = df.groupby(['albumartist', ALBUM, 'disc_int']).max('track_int').to_dict()['track_int']

    df[TRACKNUMBER] = df[['track_int', 'albumartist', ALBUM, 'disc_int']].apply(
        lambda x: create_combined_track_nr(x[0], x[1], x[2], x[3], max_track_dict), axis=1)

    df.drop(['track_int', 'disc_int'], axis=1, inplace=True)

    if del_albumartist:
        df.drop(['albumartist'], axis=1, inplace=True)


def set_combined_disc_number(df: pd.DataFrame) -> None:
    df[DISCNUMBER] = df[DISCNUMBER].fillna(1)
    df['disc_int'] = df[DISCNUMBER].map(lambda x: track_number_from_track_total_track_combination(x))

    if 'albumartist' not in df.columns:
        df['albumartist'] = df['artist']
        del_albumartist = True
    else:
        del_albumartist = False

    max_disc_dict = df.groupby(['albumartist', ALBUM]).max('disc_int').to_dict()['disc_int']

    df[DISCNUMBER] = df[['disc_int', 'albumartist', ALBUM]].apply(
        lambda x: create_combined_disc_nr(x[0], x[1], x[2], max_disc_dict), axis=1)

    df.drop(['disc_int'], axis=1, inplace=True)

    if del_albumartist:
        df.drop(['albumartist'], axis=1, inplace=True)


def extract_options(df, column):
    try:
        options = list(df[column].drop_duplicates().values)
    except KeyError:
        options = []
    return options


def collect_data(path: Path):
    results = []
    skip_counter = 0
    untagged_counter = 0
    files_total = 0
    for f in find_all_mp3s(path):
        files_total = files_total + 1
        audio = load_mp3(f)
        if audio is not None:
            results.append({**{k: v[0] for k, v in {**dict(audio)}.items()}, 'filename': BASEPATH / f})
            if not audio:
                untagged_counter = untagged_counter + 1
        else:
            skip_counter = skip_counter + 1
    return results, skip_counter, untagged_counter, files_total


def add_albumart(audio_path, image_path):
    audio = MP3(audio_path, ID3=ID3)
    #TODO: Decide on error handling
    audio.tags.add(APIC(mime='image/jpeg', type=3, desc=u'Cover', data=open(image_path, 'rb').read()))
    audio.save()  # save the current changes



if __name__ == '__main__':
    timestamp = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
    results = []
    skip_counter = 0
    untagged_counter = 0
    files_counter = 0
    folders = (BASEPATH).glob('*')

    with open('details_'+timestamp+'.txt', 'w') as f:
        for folder in folders:
            res, sc, uc, fc = collect_data(BASEPATH/folder)
            f.writelines(f"Entering folder {str(folder)}.\n")
            for entry in res:
                entry['filename'] = str(entry['filename'])
                results = results + [entry]
            skip_counter = skip_counter + sc
            untagged_counter = untagged_counter + uc
            files_counter = files_counter + fc
            if sc != 0:
                f.writelines(f"{sc} files skipped in this folder. Now {skip_counter} files skipped in total.\n")
            if uc !=0:
                f.writelines(f"{uc} files without tags in this folder. Now {untagged_counter} without tags in total\n")

    with open('summary_'+timestamp+'.txt', 'w') as f:
        f.writelines("======================\n")
        f.writelines(f"{files_counter} mp3s analyzed\n")
        f.writelines(f"{len(results)} mp3s were added to table\n")
        f.writelines(f"{skip_counter} files skipped\n")
        f.writelines(f"Out of the ingested, {untagged_counter} completely untagged\n")

    with open('data_'+timestamp+'.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)