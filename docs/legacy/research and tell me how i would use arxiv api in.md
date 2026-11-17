<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# research and tell me how i would use arxiv api in python

Here's how to use the arXiv API in Python using the official `arxiv` wrapper package (by Lukas Schwab), which is the most popular and well-maintained option:

## 1. Install the package

```bash
pip install arxiv
```


## 2. Basic usage: search for papers

```python
import arxiv

# Create the API client
client = arxiv.Client()

# Define a search query
search = arxiv.Search(
    query="quantum",           # search term
    max_results=10,            # number of papers to return
    sort_by=arxiv.SortCriterion.SubmittedDate  # sort by most recent
)

# Get results (generator)
results = client.results(search)

# Iterate over papers
for paper in results:
    print(paper.title)
    print(paper.authors)
    print(paper.published)
    print(paper.pdf_url)
```


## 3. Search by paper ID (arXiv ID)

```python
# Search for a specific paper using its arXiv ID (e.g., "1605.08386v1")
search_by_id = arxiv.Search(id_list=["1605.08386v1"])
paper = next(client.results(search_by_id))

print(paper.title)  # e.g., "Attention Is All You Need"
```


## 4. Download PDF or source

```python
paper = next(client.results(arxiv.Search(id_list=["1605.08386v1"])))

# Download PDF to current directory
paper.download_pdf()

# Download PDF with custom filename
paper.download_pdf(filename="my-paper.pdf")

# Download PDF to specific directory
paper.download_pdf(dirpath="./papers", filename="my-paper.pdf")

# Download source tar.gz
paper.download_source(filename="my-paper.tar.gz")
```


## 5. Advanced query syntax

You can use structured queries:

```python
# Search by author and title
search = arxiv.Search(query="au:del_maestro AND ti:checkerboard")

# Search by category (e.g., cs.LG for Machine Learning)
search = arxiv.Search(query="cat:cs.LG", max_results=20)

# Multiple categories
search = arxiv.Search(query="cat:cs.CV OR cat:cs.CL OR cat:cs.LG", max_results=50)
```


## 6. Custom client (for rate limiting)

```python
# Slower client with larger page size and more retries
custom_client = arxiv.Client(
    page_size=100,
    delay_seconds=5.0,  # seconds between requests
    num_retries=5
)

papers = custom_client.results(arxiv.Search(query="LLM", max_results=50))
```


## 7. Example: fetch ML papers and save to CSV

```python
import arxiv
import pandas as pd

client = arxiv.Client()

search = arxiv.Search(
    query="cat:cs.LG",
    max_results=50,
    sort_by=arxiv.SortCriterion.SubmittedDate,
    sort_order=arxiv.SortOrder.Descending
)

papers = []
for paper in client.results(search):
    papers.append({
        "title": paper.title,
        "authors": ", ".join(str(a) for a in paper.authors),
        "published": paper.published.isoformat(),
        "arxiv_id": paper.get_id(),
        "pdf_url": paper.pdf_url,
        "summary": paper.summary[:200]
    })

df = pd.DataFrame(papers)
df.to_csv("arxiv_ml_papers.csv", index=False)
```

This fits your workflow since you already use Jupyter, Python, and pandas for data science tasks.

For more details, see the full docs: [arxiv.py documentation](https://lukasschwab.me/arxiv.py/) [^1_1]
<span style="display:none">[^1_10][^1_2][^1_3][^1_4][^1_5][^1_6][^1_7][^1_8][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: https://lukasschwab.me/arxiv.py/

[^1_2]: https://mukhlisraza.medium.com/how-to-export-arxiv-papers-with-pythons-atom-api-e084c2970484

[^1_3]: https://github.com/lukasschwab/arxiv.py

[^1_4]: https://pypi.org/project/arxiv/

[^1_5]: https://pypi.org/project/arxiv/1.4.8/

[^1_6]: https://medium.com/analytics-vidhya/geek-harder-using-this-python-arxiv-api-wrapper-ca9003b85b24

[^1_7]: https://reference.langchain.com/python/langchain-community/utilities/arxiv/ArxivAPIWrapper

[^1_8]: https://www.youtube.com/watch?v=e9TSnAZAXOo

[^1_9]: https://www.askpython.com/python/examples/scrape-arxiv-papers-python

[^1_10]: https://github.com/titipata/arxivpy


---

# what are the exact things we can do using their API

The arXiv API gives you **programmatic access to over 1 million papers** across physics, math, computer science, and other fields. Here are the **exact operations** you can perform:

## 1. Search for Papers

| Search Type | Query Format | Example |
| :-- | :-- | :-- |
| **All fields** | `all:term` | `all:electron` searches title, abstract, authors, comments, journal ref [^2_1][^2_2] |
| **Title only** | `ti:term` | `ti:"quantum criticality"` [^2_1] |
| **Author** | `au:firstname_lastname` | `au:del_maestro` [^2_1] |
| **Abstract** | `abs:term` | `abs:machine learning` [^2_1] |
| **Category** | `cat:category` | `cat:cs.LG` (ML) or `cat:cs.CV` (computer vision) [^2_1] |
| **Comment** | `co:term` | `co:"23 pages"` [^2_1] |
| **Journal Ref** | `jr:term` | `jr:"Eur.Phys.J"` [^2_1] |

### Boolean Operators

| Operator | Usage | Example |
| :-- | :-- | :-- |
| `AND` | Both terms required | `au:del_maestro AND ti:checkerboard` [^2_1] |
| `OR` | Either term | `cat:cs.CV OR cat:cs.CL` [^2_1] |
| `ANDNOT` | Exclude term | `au:del_maestro ANDNOT ti:checkerboard` [^2_1] |

### Date Range Filtering

```
submittedDate:[YYYYMMDDHHMM+TO+YYYYMMDDHHMM]
```

Example: `au:del_maestro AND submittedDate:[202301010600+TO+202401010600]`[^2_1]

[^2_1]

## 2. Fetch by Paper ID

- Get **latest version**: `id_list=1605.08386`
- Get **specific version**: `id_list=1605.08386v1`
- Get **multiple papers**: `id_list=1605.08386,2301.12345`

[^2_3][^2_1]

## 3. Pagination (Get Large Result Sets)

| Parameter | Default | Max | Description |
| :-- | :-- | :-- | :-- |
| `start` | 0 | ∞ | 0-based index of first result [^2_1] |
| `max_results` | 10 | 2000 per call | Number of results per request [^2_1] |

Max total results: **30,000** (must fetch in slices of ≤2000)[^2_1]

Example pagination:

- `start=0, max_results=10` → results 0-9
- `start=10, max_results=10` → results 10-19
- `start=20, max_results=10` → results 20-29

[^2_1]

## 4. Sort Results

| `sortBy` | Description |
| :-- | :-- |
| `relevance` | Apache Lucene relevance (default) [^2_1] |
| `lastUpdatedDate` | When paper was updated |
| `submittedDate` | When paper was submitted |

| `sortOrder` | Description |
| :-- | :-- |
| `ascending` | Oldest first |
| `descending` | Newest first (default) |

Example: `sortBy=submittedDate&sortOrder=descending`[^2_4][^2_1]

## 5. Retrieve Paper Metadata

For each paper, you get:


| Field | XML Element | Description |
| :-- | :-- | :-- |
| Title | `<title>` | Paper title [^2_1] |
| Abstract | `<summary>` | Full abstract [^2_1] |
| Authors | `<author><name>` | List of authors in order [^2_1] |
| Author affiliation | `<arxiv:affiliation>` | If provided [^2_1] |
| Publication date (v1) | `<published>` | Date version 1 was submitted [^2_1] |
| Update date | `<updated>` | Date this version was submitted [^2_1] |
| arXiv ID | `<id>` | URL like `http://arxiv.org/abs/1605.08386` [^2_1] |
| Categories | `<category>` | All categories (cs.LG, cs.AI, etc.) [^2_1] |
| Primary category | `<arxiv:primary_category>` | Main classification [^2_1] |
| Author comments | `<arxiv:comment>` | e.g., "23 pages, 8 figures" [^2_1] |
| Journal reference | `<arxiv:journal_ref>` | Published venue if available [^2_1] |
| DOI | `<arxiv:doi>` | Resolved DOI link [^2_1] |
| PDF URL | `<link title="pdf">` | Direct PDF download link [^2_1] |
| Abstract page | `<link rel="alternate">` | arXiv HTML page [^2_1] |

[^2_3][^2_1]

## 6. Get Total Results Count

```xml
<opensearch:totalResults>1000</opensearch:totalResults>
```

Returns total matching papers for your query[^2_1]

## 7. Download Papers

Via the Python wrapper:

```python
paper.download_pdf()              # Download PDF
paper.download_pdf(filename="x.pdf")  # Custom filename
paper.download_source()           # Download source tar.gz
```


## 8. Build Custom Feeds

Create **custom RSS/Atom feeds** based on your search query:

```python
# Example: feed for "quantum computing" papers
query = "all:quantum AND cat:quant-ph"
# API returns Atom feed you can use in feed readers
```

This lets you notify users about new papers matching your criteria[^2_1]

## 9. Filter Results

Combine `search_query` + `id_list`:

- Returns papers **in `id_list`** that **also match `search_query`**
- Useful for validating/filtering existing paper lists[^2_1]

| `search_query` | `id_list` | Returns |
| :-- | :-- | :-- |
| ✅ present | ❌ blank | All papers matching query [^2_1] |
| ❌ blank | ✅ present | Papers in id_list [^2_1] |
| ✅ present | ✅ present | Papers in id_list matching query [^2_1] |

## 10. Handle Errors

Errors return Atom feeds with:

- `<summary>`: Error message
- `<link>`: URL to detailed explanation

Common errors:

- Invalid `start`/`max_results` (must be integer ≥ 0)
- Malformed arXiv IDs
- `max_results` > 30,000 → HTTP 400[^2_1]


## What You **Cannot** Do

| Limitation | Explanation |
| :-- | :-- |
| No direct year filter | Must use `submittedDate` range or post-filter by `<published>` [^2_4] |
| No full-text search | Only metadata (title, abstract, authors, etc.) [^2_1] |
| Max 30,000 results | Queries with more must be refined [^2_1] |
| 3-second delay recommended | For multiple consecutive calls [^2_1] |

## Terms of Use

You **can**:

- Retrieve/store/transform/share **metadata** for personal use or research[^2_3]
- Retrieve/use **paper content** for personal use or research[^2_3]
- Build tools for discovery/notifications (search interfaces, mobile apps, visualizations, citation graphs)[^2_3]

You **cannot**:

- Reproduce copyrighted full text without permission
- Use for commercial purposes without explicit approval

Full terms: [arXiv API Terms of Use](https://info.arxiv.org/help/api/index.html)[^2_5]

This API is perfect for building literature-review pipelines, NLP datasets, research dashboards, or academic notification systems—common use cases for AI/ML researchers like yourself.[^2_6]
<span style="display:none">[^2_10][^2_11][^2_12][^2_7][^2_8][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://info.arxiv.org/help/api/user-manual.html

[^2_2]: https://info.arxiv.org/help/api/basics.html

[^2_3]: https://note.com/mega_gorilla/n/n5d8f74baf09e?hl=en

[^2_4]: https://stackoverflow.com/questions/64047299/how-to-query-arxiv-for-a-specific-year

[^2_5]: https://info.arxiv.org/help/api/index.html

[^2_6]: https://mukhlisraza.medium.com/how-to-export-arxiv-papers-with-pythons-atom-api-e084c2970484

[^2_7]: https://arxiv.org/html/2402.05102v2

[^2_8]: https://reference.langchain.com/python/langchain-community/utilities/arxiv/ArxivAPIWrapper

[^2_9]: https://pypi.org/project/arxiv/1.4.8/

[^2_10]: https://www.pdfvector.com/blog/8-extract-arxiv-paper-metadata-from-xml-responses

[^2_11]: https://arxiv.github.io/arxiv-submission-core/submission_api_context.html

[^2_12]: https://github.com/lukasschwab/arxiv.py

