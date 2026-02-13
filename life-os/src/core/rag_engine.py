import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path
from src.core.config import settings
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGClient:
    def __init__(self):
        # Persistent storage for embeddings
        self.db_path = Path(settings.KNOWLEDGE_BASE_PATH) / ".life-os-db"
        self.client = chromadb.PersistentClient(path=str(self.db_path))

        # Use a default sentence transformer model for embeddings
        # This will download the model on first run (approx 400MB)
        self.ef = embedding_functions.DefaultEmbeddingFunction()

        self.collection = self.client.get_or_create_collection(
            name="life_os_knowledge",
            embedding_function=self.ef
        )

    def index_knowledge_base(self):
        """
        Scans Logs/ and Projects/ for .md files and indexes them.
        In a real app, we'd check modification times to avoid re-indexing unchanged files.
        """
        logger.info("Indexing knowledge base...")
        kb_path = Path(settings.KNOWLEDGE_BASE_PATH)

        files_to_index = []
        files_to_index.extend(kb_path.glob("Logs/**/*.md"))
        files_to_index.extend(kb_path.glob("Projects/**/*.md"))
        files_to_index.extend(kb_path.glob("Projects/**/context.yaml")) # Index context too

        documents = []
        metadatas = []
        ids = []

        for file_path in files_to_index:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if content.strip():
                        documents.append(content)
                        metadatas.append({"source": str(file_path.name), "path": str(file_path)})
                        ids.append(str(file_path)) # Use path as unique ID
            except Exception as e:
                logger.warning(f"Failed to read {file_path}: {e}")

        if documents:
            # Upsert (update or insert)
            # Batching might be needed for huge datasets, but fine for personal use
            self.collection.upsert(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Indexed {len(documents)} documents.")
        else:
            logger.info("No documents found to index.")

    def search(self, query, n_results=3):
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )

        # Format results
        context_snippets = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i]
                context_snippets.append(f"Source: {meta['source']}\nContent: {doc[:1000]}...") # Limit context length

        return "\n\n".join(context_snippets)

if __name__ == "__main__":
    rag = RAGClient()
    rag.index_knowledge_base()
    print(rag.search("Project updates"))
