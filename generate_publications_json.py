import json
from pathlib import Path
import bibtexparser
from bibtexparser.bparser import BibTexParser

parser = BibTexParser()
parser.ignore_nonstandard_types = False


BIB_FILE = Path("publications.bib")
OUT_FILE = Path("src/data/publications.json")


def clean_text(text):
    if not text:
        return ""
    return (
        text.replace("{", "")
        .replace("}", "")
        .replace("\n", " ")
        .strip()
    )


'''def format_authors(author_field):
    if not author_field:
        return ""

    authors = [a.strip() for a in author_field.split(" and ")]

    formatted = []
    for author in authors:
        if "," in author:
            last, first = [x.strip() for x in author.split(",", 1)]
            formatted.append(f"{first} {last}")
        else:
            formatted.append(author)

    return ", ".join(formatted)'''


def make_link(entry):
    url = entry.get("url", "").strip()
    doi = entry.get("doi", "").strip()

    if url:
        return url

    if doi:
        if doi.startswith("http"):
            return doi
        return f"https://doi.org/{doi}"

    return ""


def get_status(entry):
    entry_type = entry.get("ENTRYTYPE", "")
    keywords = clean_text(entry.get("keywords", "")).lower()
    pubstate = clean_text(entry.get("pubstate", "")).lower()

    if entry_type in ["Preprint", "preprint", "online", "online not standard"]:
        return "preprint"
    
    if entry_type in ["Manuscript", "manuscript", "unpublished"]:
        return "in_preparation"

    return "published"

def get_year(entry):
    if entry.get("year"):
        return clean_text(entry["year"])

    if entry.get("date"):
        return clean_text(entry["date"][:4])

    return ""

def get_venue(entry):
    entry_type = entry.get("ENTRYTYPE", "").lower()

    if entry_type == "online":
        return clean_text(
            entry.get("note").split(" ")[0]
            or entry.get("organization")
            or entry.get("publisher")
            or entry.get("journaltitle")
            or entry.get("journal")
            or "Preprint"
        )

    return clean_text(
        entry.get("shortjournal")
        or entry.get("shortjournaltitle")
        or entry.get("journalabbr")
        or entry.get("journaltitle")
        or entry.get("journal")
        or entry.get("booktitle")
        or ""
    )
    
def clean_pages(pages):
    if not pages:
        return ""

    return (
        pages.replace("--", "–")  # en dash
        .replace("{", "")
        .replace("}", "")
        .strip()
    )
    
def format_volume_issue_pages(entry):
    volume = clean_text(entry.get("volume", ""))
    issue = clean_text(entry.get("number", "") or entry.get("issue", ""))
    pages = clean_pages(entry.get("pages", ""))

    parts = []

    if volume:
        if issue:
            parts.append(f"{volume}({issue})")
        else:
            parts.append(volume)

    if pages:
        parts.append(pages)

    return ", ".join(parts)

'''MY_NAMES = [
    "Maité Crespo-García",
    "Maité Crespo-Garcı́a",
    "Maite Crespo Garcia",
    "Maite Crespo-Garcia",
]'''

MY_NAMES = [
    "Crespo-García M",
    "Crespo-Garcı́a M",
]

def highlight_me(authors):
    for name in MY_NAMES:
        authors = authors.replace(name, f"<strong>{name}</strong>")
    return authors

def format_one_author(author):
    author = author.strip()

    if "," in author:
        surname, given = [x.strip() for x in author.split(",", 1)]
    else:
        parts = author.split()
        surname = parts[-1]
        given = " ".join(parts[:-1])

    initials = "".join([part[0] for part in given.replace("-", " ").split() if part])

    return f"{surname} {initials}"


def format_authors(author_field):
    if not author_field:
        return ""

    authors = [a.strip() for a in author_field.split(" and ")]
    formatted = [format_one_author(author) for author in authors]

    formatted = [
        f"<strong>{author}</strong>" if author in MY_NAMES else author
        for author in formatted
    ]

    return ", ".join(formatted) + "."

def parse_publication(entry):
    authors = format_authors(entry.get("author", ""))
    #authors = highlight_me(authors)
    return {
        "id": entry.get("ID", ""),
        "type": entry.get("ENTRYTYPE", ""),
        "status": get_status(entry),
        "year": get_year(entry),
        "date": clean_text(entry.get("date", "")),
        "title": clean_text(entry.get("title", "")),
        "authors": authors,
        "venue": get_venue(entry),
        "volume_issue_pages": format_volume_issue_pages(entry),
        "journal": clean_text(
            entry.get("journaltitle")
            or entry.get("journal")
            or entry.get("booktitle")
            or ""
        ),
        "volume": clean_text(entry.get("volume", "")),
        "number": clean_text(entry.get("number", "")),
        "pages": clean_pages(entry.get("pages", "")),
        "doi": clean_text(entry.get("doi", "")),
        "url": clean_text(entry.get("url", "")),
        "link": make_link(entry),
        "pdf": clean_text(entry.get("pdf", "")),
        "code": clean_text(entry.get("code", "")),
        "abstract": clean_text(entry.get("abstract", "")),
        "showAbstract": bool(entry.get("abstract", "")),
    }


def main():
    with open(BIB_FILE, encoding="utf-8") as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file, parser=parser)
        
    '''for entry in bib_database.entries:
        print(entry["ENTRYTYPE"], entry["ID"])'''

    publications = [parse_publication(entry) for entry in bib_database.entries]

    publications.sort(
        key=lambda pub: int(pub["year"]) if pub["year"].isdigit() else 0,
        reverse=True,
    )

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(publications, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(publications)} publications to {OUT_FILE}")


if __name__ == "__main__":
    main()