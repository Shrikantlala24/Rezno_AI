from typing import List
from models import RankedPaper


def generate_bibtex(papers: List[RankedPaper]) -> str:
    """Generate BibTeX formatted string for a list of RankedPaper objects."""
    entries = []
    for p in papers:
        clean_key = p.arxiv_id.replace(".", "_").replace("/", "_")
        authors_str = " and ".join(p.authors) if p.authors else "Unknown"
        year = p.published[:4] if len(p.published) >= 4 else "2024"
        url = p.pdf_url or p.abs_url

        entry = (
            f"@article{{{clean_key},\n"
            f"  title = {{{p.title}}},\n"
            f"  author = {{{authors_str}}},\n"
            f"  journal = {{arXiv preprint arXiv:{p.arxiv_id}}},\n"
            f"  year = {{{year}}},\n"
            f"  eprint = {{{p.arxiv_id}}},\n"
            f"  url = {{{url}}}\n"
            f"}}"
        )
        entries.append(entry)

    return "\n\n".join(entries)
