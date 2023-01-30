import argparse
import json
import logging
import tarfile
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path

from en.extract_kindle_lemmas import create_kindle_lemmas_db
from en.translate import translate_english_lemmas
from extract_wiktionary import create_wiktionary_lemmas_db

VERSION = "0.5.1dev"
MAJOR_VERSION = VERSION.split(".")[0]


def compress(tar_path: Path, files: list[Path]) -> None:
    if tar_path.exists():
        tar_path.unlink()
    with tarfile.open(tar_path, "x:gz") as tar:
        for wiktionary_file in files:
            tar.add(wiktionary_file)


def create_wiktionary_files(lemma_lang: str, gloss_lang: str = "en") -> None:
    db_paths = create_wiktionary_lemmas_db(lemma_lang, gloss_lang, MAJOR_VERSION)
    compress(
        Path(f"{lemma_lang}/wiktionary_{lemma_lang}_{gloss_lang}_v{VERSION}.tar.gz"),
        db_paths[:1],
    )
    if gloss_lang == "zh":
        compress(
            Path(f"{lemma_lang}/wiktionary_{lemma_lang}_zh_cn_v{VERSION}.tar.gz"),
            db_paths[1:],
        )


def create_kindle_files(lemma_lang: str, kaikki_json_path: Path = Path()) -> None:
    db_path = Path(f"{lemma_lang}/kindle_{lemma_lang}_en_v{MAJOR_VERSION}.db")
    create_kindle_lemmas_db(lemma_lang, kaikki_json_path, db_path)
    compress(Path(f"{lemma_lang}/kindle_{lemma_lang}_en_v{VERSION}.tar.gz"), [db_path])


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s: %(message)s", level=logging.INFO
    )
    with open("kaikki_languages.json", encoding="utf-8") as f:
        kaikki_languages = json.load(f)

    parser = argparse.ArgumentParser()
    parser.add_argument("gloss_lang", choices=["en", "zh"])
    parser.add_argument(
        "--lemma-lang-codes",
        nargs="*",
        default=kaikki_languages.keys(),
        choices=kaikki_languages.keys(),
    )
    args = parser.parse_args()

    with ProcessPoolExecutor() as executor:
        logging.info("Creating Wiktionary files")
        for ignore in executor.map(
            partial(create_wiktionary_files, gloss_lang=args.gloss_lang),
            args.lemma_lang_codes,
        ):
            pass
        logging.info("Wiktionary files created")
        if args.gloss_lang == "en":
            kaikki_json_path = Path("en/kaikki.org-dictionary-English.json")
            translate_english_lemmas(
                kaikki_json_path, set(args.lemma_lang_codes) - {"en"}
            )
            logging.info("Creating Kindle files")
            for ignore in executor.map(
                partial(create_kindle_files, kaikki_json_path=kaikki_json_path),
                args.lemma_lang_codes,
            ):
                pass
            logging.info("Kindle files created")


if __name__ == "__main__":
    main()
