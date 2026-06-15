from chroma_client import chroma_client
import json

collection = chroma_client.get_collection(name="my_collection")

# collection.add(
#     ids=["id1", "id2"],
#     documents=[
#         "This is a document about pineapple",
#         "This is a document about oranges"
#     ]
# )

results = collection.query(
    query_texts=["This is a query document about hawaii"],
    n_results=2
)
print(json.dumps(results, indent=4))