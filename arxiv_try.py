import streamlit as st
import arxiv

# Create the API client
client = arxiv.Client()

st.title("ArXiv Paper Search")

search_term = st.text_input("Enter a search term:", key="search_term")

# Define a search query
search = arxiv.Search(
    query=search_term,           # search term
    max_results=1,            # number of papers to return
    sort_by=arxiv.SortCriterion.SubmittedDate  # sort by most recent
)


def pdf_url(link_list):
    for link in link_list:
        if link.title == "pdf":
            return link
    return None


if st.button("Search"):
    st.write(f"Searching for papers related to '{search_term}'...")
    
    results = list(client.results(search))  # materialize the generator
    
    st.subheader("Search Results")
    st.divider()
    
    st.write(results[0].entry_id)
    # entry id is ->  actual Url
    st.write(results[0].updated)
    # datetime of updation
    st.write(results[0].published)
    # datetime of publication

    st.write(results[0].title)

    st.write(results[0].authors)
    st.write(results[0].summary)

    st.divider()
    st.write(results[0].comment)
    st.write(results[0].journal_ref)

    st.divider()
    st.write(results[0].doi)
    st.write(results[0].primary_category)

    st.divider()
    st.write(results[0].categories)
    st.write(results[0].links)

    st.write(pdf_url(results[0].links))



    #     entry_id: str,
    #     updated: datetime arxiv._DEFAULT_TIMEME,
    #     published: datetime = _DEFAULT_TIME,
    #     title: str = "",

    #     authors: list[Result.Author] | None = None,
    #     summary: str = "",
    #     comment: str = "",
    #     journal_ref: str = "",

    #     doi: str = "",
    #     primary_category: str = "",
    #     categories: list[str] | None = None,
    #     links: list[Result.Link] | None = None,

    st.write(type(results[0]))

