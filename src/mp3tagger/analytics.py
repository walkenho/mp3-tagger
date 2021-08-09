import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List

import pandas as pd
from mp3tagger.core import BASEPATH, find_all_mp3s, load_mp3

logging.basicConfig(format="%(asctime)s %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p")

DATAFOLDER = Path().cwd().parent.parent / "analytics"


def collect_data(path: Path):
    n_skipped = 0
    n_untagged = 0
    tags = []

    all_mp3s = find_all_mp3s(path)
    files_total = len(all_mp3s)

    for filename in all_mp3s:
        audio = load_mp3(filename)
        if audio is None:
            n_skipped = n_skipped + 1
        else:
            # convert path to str to be serializable later
            tags.append(
                {**{k: v[0] for k, v in audio.items()}, "filename": str(filename)}
            )
            if not audio:
                n_untagged = n_untagged + 1

    return tags, {
        "n_skipped": n_skipped,
        "n_untagged": n_untagged,
        "n_total": files_total,
    }


def filter_serializable_data(tags: List[dict]) -> List[dict]:
    """Filter out tags that are serializable (for example of type ASFBoolAtttributes"""
    serializable_tags = []
    for t in tags:
        try:
            json.dumps(t)
            serializable_tags.append(t)
        except TypeError:
            pass
    return serializable_tags


def run_analytics():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    results = []
    counters = []

    with open(DATAFOLDER / f"details_{timestamp}.txt", "w") as f:
        # Go down one level to have more high-grain data
        for entry in BASEPATH.glob("*"):
            if entry.is_dir():
                f.writelines(f"Entering folder {entry}.\n")
                tags, c = collect_data(entry)
                results = results + tags
                counters.append(c)
                if c["n_skipped"] != 0:
                    f.writelines(f"{c['n_skipped']} files skipped in this folder.\n")
                if c["n_untagged"] != 0:
                    f.writelines(
                        f"{c['n_untagged']} files without tags in this folder.\n"
                    )

    df_counters = pd.DataFrame(counters)

    with open(DATAFOLDER / f"summary_{timestamp}.txt", "w") as f:
        f.writelines("======================\n")
        f.writelines(f"{df_counters['n_total'].sum()} mp3s analyzed\n")
        f.writelines(f"{len(results)} mp3s were added to table\n")
        f.writelines(f"{df_counters['n_skipped'].sum()} files skipped\n")
        f.writelines(
            f"Out of the ingested, {df_counters['n_untagged'].sum()} completely untagged\n"
        )

    serializable_tags = filter_serializable_data(results)

    with open(DATAFOLDER / f"data_{timestamp}.json", "w", encoding="utf-8") as f:
        json.dump(serializable_tags, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    logging.info("Starting Analytics")
    run_analytics()
