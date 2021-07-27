import glob
from dataclasses import dataclass
from pathlib import Path

import mutagen
import pandas as pd

from mutagen.asf import ASFError
from mutagen.id3 import ID3, APIC
from mutagen.mp3 import HeaderNotFoundError

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
    return [Path(filename) for filename in glob.iglob(str(path / '**' / '*.mp3'), recursive=True)]


@dataclass
class MP3Table:
    path: Path
    data: pd.DataFrame = pd.DataFrame()

    def load(self):
        self.data = pd.DataFrame()
        for f in find_all_mp3s(self.path):
            audio = load_mp3(f)
            if audio:
                # no tags (yet)
                if not dict(audio).keys():
                    self.data = self.data.append(pd.DataFrame.from_dict({'filename': [f.relative_to(BASEPATH)]}))
                else:
                    self.data = self.data.append(pd.DataFrame.from_dict({**dict(audio), 'filename': f.relative_to(BASEPATH)}))

    def retag(self):
        for filename, row in self.data.set_index('filename').iterrows():
            #TODO: Can't this do without the **?
            tag_song(BASEPATH/filename, **row.to_dict())

    def get_entries(self, category):
        try:
            return self.data[category].unique().tolist()
        except KeyError:
            return []

    def delete_tag(self, category: str):
        """Set column entry to None. This will trigger tag deletion in tag_song"""
        self.data[category] = None

    def set_combined_track_number(self) -> None:
        grouping_columns = []

        # albums are grouped by albumartist if existent, otherwise by artist
        # (presumably equivalent to albumartist)
        # you can't just check if albumartist exists and otherwise use artist on a whole df level
        # since entry structure can be different in different albums
        if 'albumartist' in self.data.columns:
            self.data['artist_grouping_column'] = self.data['albumartist'].fillna(self.data[ARTIST])
        else:
            self.data['artist_grouping_column'] = self.data[ARTIST]
        columns_to_drop = ['artist_grouping_column']
        grouping_columns = ['artist_grouping_column', ALBUM]

        # is discnumber is present, tracks are counted by disc
        # standardize by casting strings to ints
        if DISCNUMBER in self.data.columns:
            self.data[f'{DISCNUMBER}_int'] = self.data[DISCNUMBER].fillna(1)\
                .map(lambda x: track_number_from_track_total_track_combination(x))
            grouping_columns.append(f'{DISCNUMBER}_int')
            columns_to_drop.append(DISCNUMBER)

        self.data[TRACKNUMBER] = self.data[TRACKNUMBER].map(lambda x: track_number_from_track_total_track_combination(x))

        max_track = self.data.groupby(grouping_columns)\
            [[TRACKNUMBER]]\
            .max()\
            .rename(columns={TRACKNUMBER: 'total_tracks'})
        columns_to_drop.append('total_tracks')

        self.data = self.data.join(max_track, on=grouping_columns)

        self.data[TRACKNUMBER] = self.data[[TRACKNUMBER, 'total_tracks']].astype('str').agg('/'.join, axis=1)
        self.data.drop(columns_to_drop, axis=1, inplace=True)

    def set_combined_disc_number(self) -> None:

        if DISCNUMBER in self.data.columns:
            self.data[f'{DISCNUMBER}_int'] = self.data[DISCNUMBER].fillna(1) \
                .map(lambda x: track_number_from_track_total_track_combination(x))
        else:
            # Not sure this makes much sense, buy hey ;)
            self.data[f'{DISCNUMBER}_int'] = 1

        # albums are grouped by albumartist if existent, otherwise by artist
        # (presumably equivalent to albumartist)
        # you can't just check if albumartist exists and otherwise use artist on a whole df level
        # since entry structure can be different in different albums
        if 'albumartist' in self.data.columns:
            self.data['artist_grouping_column'] = self.data['albumartist'].fillna(self.data[ARTIST])
        else:
            self.data['artist_grouping_column'] = self.data[ARTIST]

        grouping_columns = ['artist_grouping_column', ALBUM]

        max_disc = self.data.groupby(['albumartist', ALBUM])\
            [[f'{DISCNUMBER}_int']]\
            .max()\
            .rename(columns={f'{DISCNUMBER}_int': 'total_discs'})

        self.data = self.data.join(max_disc, on=grouping_columns)

        self.data[DISCNUMBER] = self.data[[f'{DISCNUMBER}_int', 'total_discs']].astype('str').agg('/'.join, axis=1)

        columns_to_drop = [f'{DISCNUMBER}_int', 'artist_grouping_column', 'total_discs']
        self.data.drop(columns_to_drop, axis=1, inplace=True)


def load_mp3(path: Path, easy=True):
    """Load mp3 file in EasyID from path. Return None if error occurs."""
    try:
        audio = mutagen.File(path, easy=easy)
        # No tags, try add empty ones:
        if audio.tags is None:
            try:
                audio.add_tags()
            except Exception as err:
                print(f"Error {err.args[0]} occured when trying to add empty tags to {path}.")
                return
        return audio
    except HeaderNotFoundError:
        print(f"Header Not Found error for {path} - Not a valid MP3 file")
    except ASFError:
        print(f"ASFError for {path}")
    except Exception as err:
        print(f"Error {err.args[0]} occured when trying to load {path}.")


def tag_song(filepath: Path, **tags) -> None:
    """
    Allowed tags:
    * album, artist, albumartist
    * date, discnumber, tracknumber, genre
    * language, encodedby, copyright
    * title, length
    * 'bpm', 'compilation', 'composer', 'lyricist', 'length', 'media', 'mood',
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
    if audio:
        for k, v in tags.items():
            if v:
                audio[k] = v
            # if no value was given in table, delete tag
            else:
                try:
                    audio.__delitem__(k)
                except KeyError:
                    # None tags are added due to the existence of tags in other mp3 in the table.
                    # If KeyError is thrown, tag did not exist in the first place, so all good :)
                    pass
        audio.save()



def track_number_from_track_total_track_combination(track_string:str) -> int:
    """Extract the numerical tracknumber from a string track number.
     Input can be of format:
    * track
    * track/total tracks
    """
    return int(str(track_string).split('/')[0])


def set_mp3_coverart(audio_path, image_path):
    """Set album art of MP3 file

    ::param
     audio_path: path of MP3 file
     image_path: path of album art image (needs to be jpeg)
    """
    # EasyID3 does not allow for image tagging, use standard ID3
    audio = load_mp3(audio_path, easy=False)

    # delete all images if existing
    # TODO: add link
    if ID3.getall('APIC'):
        ID3.delall('APIC')
    audio.tags.add(APIC(mime='image/jpeg',
                        encoding=0, # Latin1
                        type=3, # cover/front image
                        desc=u'Cover',
                        data=open(image_path, 'rb').read()))
    audio.save()


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
