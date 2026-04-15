from embedder import get_embedding

def retrieve(query, vectordb, top_k):

    query_emb = get_embedding(query)

    results = vectordb.search(query_emb, top_k=top_k)

    return results