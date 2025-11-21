from elasticsearch import Elasticsearch, helpers

es = Elasticsearch("http://localhost:9200")

# 1. Create index with explicit mapping
mappings = {
    "properties": {
        "name": {"type": "text"},
        "author": {"type": "text"},
        "release_date": {"type": "date", "format": "yyyy-MM-dd"},
        "page_count": {"type": "integer"}
    }
}
es.indices.create(index="books", mappings=mappings, ignore=400)
print("Index 'books' created (or already exists).")

# 2. Add a single document
doc = {
    "name": "Snow Crash",
    "author": "Neal Stephenson",
    "release_date": "1992-06-01",
    "page_count": 470
}
es.index(index="books", id="snow_crash", document=doc, refresh=True)
print("Added single document: Snow Crash")

# 3. Bulk add multiple documents
docs = [
    {"name": "Revelation Space", "author": "Alastair Reynolds", "release_date": "2000-03-15", "page_count": 585},
    {"name": "1984", "author": "George Orwell", "release_date": "1985-06-01", "page_count": 328},
    {"name": "Fahrenheit 451", "author": "Ray Bradbury", "release_date": "1953-10-15", "page_count": 227},
    {"name": "Brave New World", "author": "Aldous Huxley", "release_date": "1932-06-01", "page_count": 268},
    {"name": "The Handmaids Tale", "author": "Margaret Atwood", "release_date": "1985-06-01", "page_count": 311},
]
actions = [
    {"_index": "books", "_id": f"book_{i}", "_source": doc}
    for i, doc in enumerate(docs, 1)
]
helpers.bulk(es, actions, refresh=True)
print("Bulk added multiple documents.")

# 4. Get a document by ID
doc_id = "snow_crash"
retrieved = es.get(index="books", id=doc_id)
print(f"Retrieved document by ID '{doc_id}':", retrieved["_source"])

# 5. Search documents (match query)
search_res = es.search(index="books", query={"match": {"release_date": "1985-06-01"}})
print("Search for books with release_date '1985-06-01':")
for hit in search_res["hits"]["hits"]:
    print(hit["_source"])

# 6. Update a document
es.update(
    index="books",
    id="snow_crash",
    doc={"page_count": 471, "language": "EN"}
)
print("Updated 'Snow Crash' with new page_count and language.")

# 7. Delete a document
es.delete(index="books", id="book_2")  # Deletes '1984'
print("Deleted document with ID 'book_2' (1984).")

# 8. Delete the index (uncomment to run)
# es.indices.delete(index="books")
# print("Deleted index 'books'.")