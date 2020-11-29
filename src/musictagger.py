from pathlib import Path
from mp3_tagger import MP3File, VERSION_1, VERSION_2, VERSION_BOTH, MP3OpenFileError
import pandas as pd
from typing import List

BASEPATH = Path('/media/walkenho/Seagate Backup Plus Drive/Eigene Musik')


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

    - artist;
    - album;
    - song;
    - track;
    - comment;
    - year;
    - genre;
    - band (version 2.x);
    - composer (version 2.x);
    - copyright (version 2.x);
    - url (version 2.x);
    - publisher (version 2.x)
    """

    mp3 = MP3File(str(BASEPATH / filepath))
    mp3.set_version(VERSION_BOTH)

    for k, v in attrs.items():
        if k == 'track':
            mp3.set_version(VERSION_1)
            track_number = v.split('/')[0]
            setattr(mp3, k, track_number)

            mp3.set_version(VERSION_2)
            setattr(mp3, k, v)

            mp3.set_version(VERSION_BOTH)
        elif k == 'genre':
            mp3.set_version(VERSION_2)
            setattr(mp3, k, v)
            mp3.set_version(VERSION_BOTH)
        else:
            try:
                if pd.isnull(v):
                    if k == 'comment':
                        del mp3.comment
                    elif k == 'copyright':
                        del mp3.copyright
                    elif k == 'url':
                        del mp3.url
                    else:
                        setattr(mp3, k, '')
                else:
                    setattr(mp3, k, v)
            except AttributeError:
                print(filepath, k, v)
                raise AttributeError

    mp3.save()


def get_table(mypath: Path, mode: str) -> pd.DataFrame:
    data = []
    for f in find_all_mp3s(mypath):
        try:
            tags = MP3File(str(BASEPATH / f)).get_tags()
            if mode in ['v1', 'both']:
                d1 = {k + '.v1': v for k, v in tags['ID3TagV1'].items()}
            else:
                d1 = {}
            if mode in ['v2', 'both']:
                d2 = {k + '.v2': v for k, v in tags['ID3TagV2'].items()}
            else:
                d2 = {}
            data.append({'filename': f, **d1, **d2})
        except MP3OpenFileError:
            print(f"{f} is not in MP3 format")

    df = pd.DataFrame.from_dict(data)
    df = df[sorted(df.columns)]
    return df


def get_tags_from_v2(df: pd.DataFrame) -> dict:
    dfc = df.copy()
    dfc.columns = [c.split('.v2')[0] for c in dfc.columns]
    dfc.set_index('filename', inplace=True)
    d = dfc.to_dict('index')
    return d


def retag(mydict: dict) -> None:
    for path, tags in mydict.items():
        tag_song(path, **tags)


def delete_copyright(df: pd.DataFrame):
    df['copyright.v2'] = None


def delete_url(df: pd.DataFrame):
    df['url.v2'] = None


def delete_comment(df: pd.DataFrame):
    df['comment.v2'] = None


def extract_track_number(mystr):
    return int(str(mystr).split('/')[0])


def create_new_track_nr(track_int, artist, album, disk_int, mydict):
    return f"{track_int}/{mydict[(artist, album, disk_int)]}"


def create_new_disk_nr(disk_int, artist, album, mydict):
    return f"{disk_int}/{mydict[(artist, album)]}"


def set_track_and_disk_number(df):
    if 'disk.v2' not in df.columns:
        df['disk_int'] = 1
    else:
        df['disk_int'] = df['disk.v2'].map(lambda x: extract_track_number(x))

    df['track_int'] = df['track.v2'].map(lambda x: extract_track_number(x))

    max_disk_dict = df.groupby(['artist.v2', 'album.v2']).max('disk_int').to_dict()['disk_int']
    max_track_dict = df.groupby(['artist.v2', 'album.v2', 'disk_int']).max('track_int').to_dict()['track_int']

    df['track.v2'] = df[['track_int', 'artist.v2', 'album.v2', 'disk_int']].apply(
        lambda x: create_new_track_nr(x[0], x[1], x[2], x[3], max_track_dict), axis=1)
    df['disk.v2'] = df[['disk_int', 'artist.v2', 'album.v2']].apply(
        lambda x: create_new_disk_nr(x[0], x[1], x[2], max_disk_dict), axis=1)

    df.drop(['track_int', 'disk_int'], axis=1, inplace=True)