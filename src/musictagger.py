from pathlib import Path

import mutagen
import pandas as pd
from typing import List

from mutagen.asf import ASFError
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError
from mutagen.mp3 import HeaderNotFoundError, error

BASEPATH = Path('/media/walkenho/Seagate Backup Plus Drive/Eigene Musik')

DISCNUMBER = 'discnumber'
ALBUM = 'album'
GENRE = 'genre'
ARTIST = 'artist'
ENCODEDBY = 'encodedby'
COPYRIGHT = 'copyright'
TRACKNUMBER = 'tracknumber'

def find_categories() -> List[Path]:
    return [p.relative_to(BASEPATH) for p in BASEPATH.glob("*")]

def find_artists_for_category(category:str) -> List[Path]:
    return [p.relative_to(BASEPATH/category) for p in (BASEPATH/category).glob("*")]

def find_albums_for_category_and_artist(category: str, artist: str) -> List[Path]:
    return [p.relative_to(BASEPATH/category/artist) for p in (BASEPATH/category/artist).glob("*")]


def find_all_mp3s(path: Path) -> List[Path]:
    lst = []
    if path.is_dir():
        for f in path.glob("*"):
            res = find_all_mp3s(f)
            lst = lst + res
    elif str(path).lower().endswith('.mp3'):
        lst.append(path.relative_to(BASEPATH))
    return lst


def load_mp3(path: Path):
    try:
        audio = EasyID3(path)
        return audio
    except (ID3NoHeaderError):
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

    audio = load_mp3(BASEPATH/filepath)

    for k, v in attrs.items():
        audio[k] = v

    audio.save()


def get_table(path: Path) -> pd.DataFrame:
    df = pd.DataFrame()
    for f in find_all_mp3s(path):
        audio = load_mp3(BASEPATH/f)
        if audio:
            if not dict(audio).keys():
                df = df.append(pd.DataFrame.from_dict({'filename': [f]}))
            else:
                df = df.append(pd.DataFrame.from_dict({**dict(audio), 'filename': f}))
    return df


def get_tags(df: pd.DataFrame) -> dict:
    return df.set_index('filename').to_dict('index')


def retag(mydict: dict) -> None:
    for path, tags in mydict.items():
        tag_song(path, **tags)


def delete_column(df: pd.DataFrame, column: str):
    df[column] = None


def extract_track_number(mystr):
    return int(str(mystr).split('/')[0])


def create_combined_track_nr(track_int, artist, album, disc_int, mydict):
    return f"{track_int:02}/{mydict[(artist, album, disc_int)]}"


def create_combined_disc_nr(disc_int, artist, album, mydict):
    return f"{disc_int}/{mydict[(artist, album)]}"


def set_combined_track_number(df: pd.DataFrame) -> None:
    if DISCNUMBER not in df.columns:
        df['disc_int'] = 1
    else:
        df[DISCNUMBER] = df[DISCNUMBER].fillna(1)
        df['disc_int'] = df[DISCNUMBER].map(lambda x: extract_track_number(x))

    df['track_int'] = df[TRACKNUMBER].map(lambda x: extract_track_number(x))

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
    df['disc_int'] = df[DISCNUMBER].map(lambda x: extract_track_number(x))

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
    return list(df[column].drop_duplicates().values)


def collect_data(path):
    results = []
    skip_counter = 0
    untagged_counter = 0
    files_total = 0
    for f in find_all_mp3s(path):
        files_total = files_total + 1
        audio = load_mp3(BASEPATH/f)
        if audio is not None:
            results.append({**{k: v[0] for k, v in {**dict(audio)}.items()}, 'filename': BASEPATH / f})
            if not audio:
                untagged_counter = untagged_counter + 1
        else:
            skip_counter = skip_counter + 1
    return results, skip_counter, untagged_counter, files_total


if __name__ == '__main__':
    results = []
    skip_counter = 0
    untagged_counter = 0
    files_counter = 0
    folders = (BASEPATH).glob('*')
    for folder in folders:
        res, c, t, f = collect_data(BASEPATH/folder)
        print(folder)
        results = results + res
        skip_counter = skip_counter + c
        untagged_counter = untagged_counter + t
        files_counter = files_counter + f
        if c != 0:
            print(f"{c} files skipped in this folder. Now {skip_counter} files skipped in total.")
        if t !=0:
            print(f"{t} files completely untagged. Now {untagged_counter} completely untagged.")

    print(f"{files_counter} mp3s analyzed")
    print(f"{len(results)} mp3s were added to table")
    print(f"{skip_counter} files skipped")
    print(f"{files_counter} should be equal to {len(results) + skip_counter}")
    print(f"{untagged_counter} completely untagged")


    #TODO: Sth here isn't right yet. A lot of files seem to get skipped, but don't error. How can this be?
    #TODO: Use example folder for Aventura (for example).