import argparse
import json
import sys
import tarfile
from pathlib import Path

from dump_wiktionary import dump_wiktionary
from en.dump_kindle_lemmas import dump_kindle_lemmas
from extract_wiktionary import download_kaikki_json, extract_wiktionary

VERSION = "0.0.0"


def compress(lang: str, files: list[Path]) -> None:
    with tarfile.open(f"{lang}/wiktionary_{lang}_v{VERSION}.tar.gz", "x:gz") as tar:
        for wiktionary_file in files:
            tar.add(wiktionary_file)


def main():
    with open("kaikki_languages.json", encoding="utf-8") as f:
        languages = json.load(f)
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--languages", nargs="*", default=languages.keys(), choices=languages.keys()
    )
    args = parser.parse_args()

    for lang in args.languages:
        kaikki_path = download_kaikki_json(lang, languages[lang])
        if lang != "en":
            difficulty_json_path = Path(f"{lang}/difficulty.json")
            difficulty_data = {}
            if difficulty_json_path.exists():
                with open(f"{lang}/difficulty.json", encoding="utf-8") as f:
                    difficulty_data = json.load(f)
        else:
            with open("en/kindle_lemmas.json", encoding="utf-8") as f:
                difficulty_data = {
                    lemma: values[0] for lemma, values in json.load(f).items()
                }
        wiktionary_json_path, tst_path = extract_wiktionary(
            lang, kaikki_path, difficulty_data
        )
        wiktioanry_dump_path = Path(f"{lang}/wiktionary_{lang}_dump_v{VERSION}")
        print(f"Dumping {lang} Wiktionary file.")
        dump_wiktionary(wiktionary_json_path, wiktioanry_dump_path, lang)
        print(f"Compressing {lang} files.")
        compress(lang, [wiktionary_json_path, tst_path, wiktioanry_dump_path])

    if "en" in args.languages:
        print("Dumping Kindle lemmas.")
        with open("en/kindle_lemmas.json", encoding="utf-8") as f:
            lemmas = json.load(f)
            dump_kindle_lemmas(lemmas, f"en/kindle_lemmas_dump_v{VERSION}")


if __name__ == "__main__":
    sys.exit(main())
