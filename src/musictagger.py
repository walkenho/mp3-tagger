from pathlib import Path
import pandas as pd
from typing import List

from mutagen.easyid3 import EasyID3

BASEPATH = Path('/media/walkenho/Seagate Backup Plus Drive/Eigene Musik')

DISCNUMBER = 'discnumber'
ALBUM = 'album'
GENRE = 'genre'
ARTIST = 'artist'
ENCODEDBY = 'encodedby'
COPYRIGHT = 'copyright'

def find_artists() -> List[Path]:
    return [p.relative_to(BASEPATH) for p in BASEPATH.glob("*")]


def find_albums_for_artist(artist: str) -> List[Path]:
    return [p.relative_to(BASEPATH/artist) for p in (BASEPATH/artist).glob("*")]


def find_all_mp3s(path: Path) -> List[Path]:
    lst = []
    if path.is_dir():
        for f in path.glob("*"):
            res = find_all_mp3s(f)
            lst = lst + res
    elif str(path).lower().endswith('.mp3'):
        lst.append(path.relative_to(BASEPATH))
    return lst


def tag_song(filepath: Path, **attrs) -> None:
    """
    Allowed tags:
    * 'album'
    * 'artist'
    * 'albumartist'
    * 'date'
    * 'discnumber'
    * 'tracknumber'
    * 'genre'
    * 'language'
    * encodedby
    * copyright
    * title

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

    audio = EasyID3(BASEPATH / filepath)

    for k, v in attrs.items():
        audio[k] = v

    audio.save()


def get_table(path: Path) -> pd.DataFrame:
    df = pd.DataFrame.from_dict({})
    for f in find_all_mp3s(path):
        df = df.append(pd.DataFrame.from_dict({**dict(EasyID3(BASEPATH/f)), 'filename': f}))
    return df


def get_tags(df: pd.DataFrame) -> dict:
    dfc = df.copy()
    dfc.set_index('filename', inplace=True)
    d = dfc.to_dict('index')
    return d


def retag(mydict: dict) -> None:
    for path, tags in mydict.items():
        tag_song(path, **tags)


def delete_column(df: pd.DataFrame, column: str):
    df[column] = None


def extract_track_number(mystr):
    return int(str(mystr).split('/')[0])


def create_new_track_nr(track_int, artist, album, disc_int, mydict):
    return f"{track_int:02}/{mydict[(artist, album, disc_int)]}"


def create_new_disc_nr(disc_int, artist, album, mydict):
    return f"{disc_int}/{mydict[(artist, album)]}"


def set_track_and_disc_number(df):
    if DISCNUMBER not in df.columns:
        df['disc_int'] = 1
    else:
        df[DISCNUMBER] = df[DISCNUMBER].fillna(1)
        df['disc_int'] = df[DISCNUMBER].map(lambda x: extract_track_number(x))

    df['track_int'] = df['tracknumber'].map(lambda x: extract_track_number(x))

    if 'albumartist' not in df.columns:
        df['albumartist'] = df['artist']
        del_albumartist = True
    else:
        del_albumartist = False

    max_disc_dict = df.groupby(['albumartist', ALBUM]).max('disc_int').to_dict()['disc_int']
    max_track_dict = df.groupby(['albumartist', ALBUM, 'disc_int']).max('track_int').to_dict()['track_int']

    df['tracknumber'] = df[['track_int', 'albumartist', ALBUM, 'disc_int']].apply(
        lambda x: create_new_track_nr(x[0], x[1], x[2], x[3], max_track_dict), axis=1)
    df[DISCNUMBER] = df[['disc_int', 'albumartist', ALBUM]].apply(
        lambda x: create_new_disc_nr(x[0], x[1], x[2], max_disc_dict), axis=1)

    df.drop(['track_int', 'disc_int'], axis=1, inplace=True)
    if del_albumartist:
        df.drop(['albumartist'], axis=1, inplace=True)


def extract_options(df, column):
    return list(df[column].drop_duplicates().values)
