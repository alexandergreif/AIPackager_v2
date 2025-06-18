"""Knowledge base service with ChromaDB integration for RAG."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional  # Added Optional

import chromadb
from chromadb.config import Settings
from loguru import logger


@dataclass
class Document:
    """Represents a document in the knowledge base."""

    id: str
    content: str
    metadata: Dict[str, Any]


@dataclass
class SearchResult:
    """Result from document search."""

    document: Document
    score: float


class KnowledgeBase:
    """ChromaDB-based knowledge base for PSADT documentation."""

    def __init__(
        self,
        collection_name: str = "psadt_docs",
        persist_directory: str = "./chroma_db",
    ):
        """Initialize the knowledge base.

        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory to persist ChromaDB data
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory

        # Create persist directory if it doesn't exist
        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory, settings=Settings(anonymized_telemetry=False))

        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
        except ValueError:
            # Collection doesn't exist, create it
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "PSADT documentation for RAG"},
            )
            logger.info(f"Created new collection: {collection_name}")

    def add_document(self, document: Document) -> None:
        """Add a document to the knowledge base.

        Args:
            document: Document to add
        """
        try:
            self.collection.add(
                documents=[document.content],
                ids=[document.id],
                metadatas=[document.metadata],
            )
            logger.debug(f"Added document: {document.id}")
        except Exception as e:
            logger.error(f"Error adding document {document.id}: {str(e)}")
            raise

    def add_documents(self, documents: List[Document]) -> None:
        """Add multiple documents to the knowledge base.

        Args:
            documents: List of documents to add
        """
        if not documents:
            return

        try:
            self.collection.add(
                documents=[doc.content for doc in documents],
                ids=[doc.id for doc in documents],
                metadatas=[doc.metadata for doc in documents],
            )
            logger.info(f"Added {len(documents)} documents to knowledge base")
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            raise

    def search(self, query: str, top_k: int = 8) -> List[SearchResult]:
        """Search for relevant documents.

        Args:
            query: Search query
            top_k: Number of top results to return (default 8 per .clinerules)

        Returns:
            List of search results
        """
        try:
            results = self.collection.query(query_texts=[query], n_results=top_k)

            search_results = []
            if results["documents"] and results["documents"][0]:
                for _, (doc_content, doc_id, metadata, distance) in enumerate(
                    zip(
                        results["documents"][0],
                        results["ids"][0],
                        results["metadatas"][0],
                        results["distances"][0],
                    )
                ):
                    document = Document(id=doc_id, content=doc_content, metadata=metadata or {})
                    # Convert distance to similarity score (lower distance = higher similarity)
                    score = 1.0 - distance if distance <= 1.0 else 1.0 / (1.0 + distance)
                    search_results.append(SearchResult(document=document, score=score))

            logger.debug(f"Found {len(search_results)} results for query: {query[:50]}...")
            return search_results

        except Exception as e:
            logger.error(f"Error searching knowledge base: {str(e)}")
            raise

    def get_collection_count(self) -> int:
        """Get the number of documents in the collection.

        Returns:
            Number of documents
        """
        try:
            # Ensure the return type is consistently int, even if self.collection.count() is Any
            count_result = self.collection.count()
            return int(count_result) if count_result is not None else 0
        except Exception as e:
            logger.error(f"Error getting collection count: {str(e)}")
            return 0

    def index_directory(
        self, directory_path: str, file_extensions: Optional[List[str]] = None
    ) -> int:  # Changed type hint
        """Index all files in a directory.

        Args:
            directory_path: Path to directory containing documents
            file_extensions: List of file extensions to include (default: ['.md', '.txt'])

        Returns:
            Number of files indexed
        """
        if file_extensions is None:
            file_extensions = [".md", ".txt"]

        directory = Path(directory_path)
        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory_path}")
            return 0

        documents = []
        indexed_count = 0

        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in file_extensions:
                try:
                    content = file_path.read_text(encoding="utf-8")
                    if content.strip():  # Only index non-empty files
                        doc_id = str(file_path.relative_to(directory))
                        metadata = {
                            "filename": file_path.name,
                            "filepath": str(file_path),
                            "extension": file_path.suffix,
                            "size": file_path.stat().st_size,
                        }

                        document = Document(id=doc_id, content=content, metadata=metadata)
                        documents.append(document)
                        indexed_count += 1

                except Exception as e:
                    logger.warning(f"Error reading file {file_path}: {str(e)}")
                    continue

        if documents:
            self.add_documents(documents)
            logger.info(f"Indexed {indexed_count} files from {directory_path}")

        return indexed_count

    def clear_collection(self) -> None:
        """Clear all documents from the collection."""
        try:
            # Delete the collection and recreate it
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "PSADT documentation for RAG"},
            )
            logger.info(f"Cleared collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error clearing collection: {str(e)}")
            raise


def get_knowledge_base() -> KnowledgeBase:
    """Factory function to get knowledge base instance.

    Returns:
        KnowledgeBase instance
    """
    return KnowledgeBase()


def initialize_knowledge_base(docs_directory: str = "docs/raw") -> KnowledgeBase:
    """Initialize knowledge base and index documentation.

    Args:
        docs_directory: Directory containing PSADT documentation

    Returns:
        Initialized KnowledgeBase instance
    """
    kb = get_knowledge_base()

    # Check if collection is empty and needs indexing
    if kb.get_collection_count() == 0:
        logger.info("Knowledge base is empty, indexing documentation...")
        indexed_count = kb.index_directory(docs_directory)
        if indexed_count > 0:
            logger.info(f"Successfully indexed {indexed_count} documents")
        else:
            logger.warning("No documents were indexed")
    else:
        logger.info(f"Knowledge base already contains {kb.get_collection_count()} documents")

    return kb
