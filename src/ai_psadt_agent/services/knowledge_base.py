"""Knowledge base service with ChromaDB integration for RAG."""

import json  # For converting dict to string for ChromaDB
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
import yaml  # For loading switches.yaml
from chromadb.config import Settings
from chromadb.errors import NotFoundError
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
        except (ValueError, NotFoundError):
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
                    score = (
                        1.0 - distance
                        if distance is not None and distance <= 1.0
                        else (1.0 / (1.0 + (distance or 0.0)) if distance is not None else 0.0)
                    )
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

    def index_directory(self, directory_path: str, file_extensions: Optional[List[str]] = None) -> int:
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
                            "type": "documentation",
                        }
                        documents.append(Document(id=doc_id, content=content, metadata=metadata))
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
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "PSADT documentation for RAG"},
            )
            logger.info(f"Cleared collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error clearing collection: {str(e)}")
            raise

    def _parse_switch_config_item(
        self, product_name: str, config_item: Dict[str, Any], index: int, yaml_file_name: str
    ) -> Optional[Document]:
        """Parses a single switch configuration item and creates a Document."""
        if not isinstance(config_item, dict):
            logger.warning(f"Skipping invalid config item for product '{product_name}': {config_item}")
            return None

        doc_id = f"switch_{product_name.lower().replace(' ', '_').replace('.', '_')}_{index}"
        content = json.dumps(config_item)
        metadata: Dict[str, Any] = {
            "type": "switch_config",
            "product_name": product_name,
            "installer_type": config_item.get("installer_type", "unknown"),
            "source_file": yaml_file_name,
        }
        if "file_pattern" in config_item:
            metadata["file_pattern"] = config_item["file_pattern"]
        return Document(id=doc_id, content=content, metadata=metadata)

    def load_switches_from_yaml(self, yaml_path: str) -> int:
        """Load switch configurations from a YAML file into ChromaDB.

        Args:
            yaml_path: Path to the YAML file.

        Returns:
            Number of switch configurations loaded.
        """
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                switches_data = yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Switches YAML file not found: {yaml_path}")
            return 0
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file {yaml_path}: {e}")
            return 0
        except Exception as e:  # Catch any other unexpected errors during file loading/parsing
            logger.error(f"Unexpected error loading YAML file {yaml_path}: {e}")
            return 0

        if not switches_data:
            logger.warning(f"No data found in switches YAML file: {yaml_path}")
            return 0

        documents_to_add: List[Document] = []
        yaml_file_name = Path(yaml_path).name

        for product_name, configs_for_product in switches_data.items():
            configs_list: List[Dict[str, Any]] = []
            if isinstance(configs_for_product, dict):
                configs_list = [configs_for_product]
            elif isinstance(configs_for_product, list):
                configs_list = configs_for_product  # This was the line with the bad type: ignore
            else:
                logger.warning(
                    f"Unexpected data type for product '{product_name}' in YAML: {type(configs_for_product)}"
                )
                continue

            for i, config_item in enumerate(configs_list):
                doc = self._parse_switch_config_item(product_name, config_item, i, yaml_file_name)
                if doc:
                    documents_to_add.append(doc)

        loaded_count = 0
        if documents_to_add:
            final_documents: List[Document] = []
            current_ids_in_batch: set[str] = set()  # Type annotation added
            for doc in documents_to_add:
                if doc.id not in current_ids_in_batch:
                    final_documents.append(doc)
                    current_ids_in_batch.add(doc.id)
                else:
                    logger.warning(f"Duplicate ID generated in current batch, skipping: {doc.id}")

            if final_documents:
                self.add_documents(final_documents)
                loaded_count = len(final_documents)
                logger.info(f"Loaded {loaded_count} switch configurations from {yaml_path}")
            else:
                logger.info(f"No new unique switch configurations to load from {yaml_path}")

        return loaded_count

    def find_switches(self, product_name: str, exe_name: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """Find silent install switches for a given product and optionally an executable name.

        Args:
            product_name: The name of the product (e.g., "Google Chrome", "7-Zip").
            exe_name: The name of the installer executable (e.g., "ChromeSetup.exe").
            top_k: Maximum number of switch configurations to return.

        Returns:
            A list of switch configuration dictionaries.
        """
        query_text = f"Silent install switches for {product_name}"
        if exe_name:
            query_text += f" installer file {exe_name}"

        where_filter = {"$and": [{"type": {"$eq": "switch_config"}}, {"product_name": {"$eq": product_name}}]}

        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=top_k * 2,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )

            found_switches: List[Dict[str, Any]] = []
            if results["documents"] and results["documents"][0]:
                for doc_str, metadata in zip(results["documents"][0], results["metadatas"][0]):
                    if metadata and metadata.get("type") == "switch_config":
                        try:
                            switch_info = json.loads(doc_str)
                            switch_info["_source_metadata"] = metadata
                            found_switches.append(switch_info)
                        except json.JSONDecodeError:
                            logger.warning(f"Could not parse switch data from ChromaDB document: {doc_str}")

            if exe_name and found_switches:
                filtered_by_exe = []
                for sw_info in found_switches:
                    pattern = sw_info.get("_source_metadata", {}).get("file_pattern")
                    if pattern and exe_name.lower() in pattern.lower():
                        filtered_by_exe.append(sw_info)
                    elif not pattern:
                        filtered_by_exe.append(sw_info)
                if filtered_by_exe:
                    found_switches = filtered_by_exe

            logger.debug(
                f"Found {len(found_switches)} switch configurations for product: '{product_name}'"
                f"{f', exe: {exe_name}' if exe_name else ''} after filtering."
            )
            return found_switches[:top_k]

        except Exception as e:
            logger.error(f"Error searching for switches for '{product_name}': {str(e)}")
            return []


def get_knowledge_base() -> KnowledgeBase:
    """Factory function to get knowledge base instance."""
    return KnowledgeBase()


def initialize_knowledge_base(
    docs_directory: str = "docs/raw", switches_yaml_path_str: Optional[str] = None
) -> KnowledgeBase:
    """Initialize knowledge base, index documentation, and load switches.

    Args:
        docs_directory: Directory containing PSADT documentation.
        switches_yaml_path_str: Optional path to the switches.yaml file.

    Returns:
        Initialized KnowledgeBase instance.
    """
    kb = get_knowledge_base()
    current_count = kb.get_collection_count()
    needs_doc_indexing = True

    if current_count > 0:
        doc_results = kb.collection.get(limit=1, where={"type": "documentation"})
        if doc_results and doc_results["ids"]:
            needs_doc_indexing = False
            logger.info(f"Documentation seems to be already indexed. Found: {doc_results['ids']}")

    if needs_doc_indexing:
        logger.info("Knowledge base may need documentation indexing...")
        indexed_count = kb.index_directory(docs_directory)
        if indexed_count > 0:
            logger.info(f"Successfully indexed {indexed_count} documentation files.")
        else:
            logger.warning(f"No new documentation files were indexed from {docs_directory}.")
    else:
        logger.info(f"Knowledge base already contains {current_count} items, and documentation appears to be indexed.")

    effective_switches_yaml_path = (
        Path(switches_yaml_path_str)
        if switches_yaml_path_str
        else Path(__file__).parent.parent / "resources" / "switches.yaml"
    )

    if effective_switches_yaml_path.exists():
        logger.info(f"Loading switches from {effective_switches_yaml_path}")
        switch_results = kb.collection.get(limit=1, where={"type": "switch_config"})
        if switch_results and switch_results["ids"]:
            logger.info(f"Switches seem to be already loaded. Found: {switch_results['ids']}")
        else:
            loaded_switches_count = kb.load_switches_from_yaml(str(effective_switches_yaml_path))
            if loaded_switches_count > 0:
                logger.info(f"Successfully loaded {loaded_switches_count} switch configurations.")
            else:
                logger.warning(f"No switch configurations were loaded from {effective_switches_yaml_path}.")
    else:
        logger.warning(f"Switches YAML file not found at {effective_switches_yaml_path}")

    return kb
