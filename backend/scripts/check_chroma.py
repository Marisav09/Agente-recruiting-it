import chromadb

persist = r'D:/User/Documents/Escs/data science/2026/desarrollo de sistemas de ia/sistema experto/bsck-ftony - copia/data/chroma_db'
client = chromadb.PersistentClient(path=persist)
try:
    coll = client.get_collection(name='candidates')
    print('collection_count=', coll.count())
except Exception as e:
    print('error:', e)
