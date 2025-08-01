import os
import json
from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
import logging
from pathlib import Path
import re
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ManualSearchTool:
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2"):
        # Resolve data/vector_store relative to root
        base_dir = Path(__file__).resolve().parents[1]
        self.vector_store_dir = base_dir / "data" / "vector_store"
        self.embedding_model = embedding_model
        self.vector_store = None
        self.embeddings = None
        self._initialize_tool()

    def _initialize_tool(self) -> None:
        logger.info("Initializing Manual Search Tool...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.embedding_model,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        if not self.vector_store_dir.exists():
            raise FileNotFoundError(f"Vector store directory not found: {self.vector_store_dir}")
        self.vector_store = Chroma(
            persist_directory=str(self.vector_store_dir),
            embedding_function=self.embeddings,
            collection_name="technical_manuals"
        )
        logger.info("Manual Search Tool initialized successfully!")

    def search(self, query: str, top_k: int = 5, filter_metadata: Optional[Dict] = None) -> List[Dict[str, Any]]:
        logger.info(f"Searching for: '{query}' (top_k={top_k})")
        if not query.strip():
            logger.warning("Empty query provided")
            return []

        processed_query = self._preprocess_query(query)

        results = self.vector_store.similarity_search_with_score(
            processed_query,
            k=top_k,
            filter=filter_metadata if filter_metadata else None
        )

        formatted_results = []
        for i, (doc, score) in enumerate(results):
            result = {
                "content": doc.page_content,
                "metadata": {
                    "source": doc.metadata.get('source_file', 'Unknown'),
                    "page": doc.metadata.get('page_number', 'Unknown'),
                },
                "relevance_score": float(1 - score),
                "rank": i + 1
            }
            formatted_results.append(result)

        logger.info(f"Found {len(formatted_results)} results")
        return formatted_results

    def _preprocess_query(self, query: str) -> str:
        query_mapping = {
            'temp': 'temperature',
            'press': 'pressure',
            'vib': 'vibration',
            'rpm': 'rotations per minute',
            'psi': 'pressure',
            'err': 'error',
            'troubleshoot': 'troubleshooting diagnosis problem',
            'fix': 'repair solution troubleshooting',
            'alarm': 'error alarm warning',
            'fault': 'error fault problem',
            'maintenance': 'maintenance service repair',
            'calibration': 'calibration adjustment setup',
            'installation': 'installation setup configuration'
        }
        processed_query = query.lower()
        for abbr, full_form in query_mapping.items():
            processed_query = re.sub(r'\b' + abbr + r'\b', full_form, processed_query)
        return processed_query

    def search_by_error_code(self, error_code: str, top_k: int = 3) -> List[Dict[str, Any]]:
        query = f"error code {error_code} troubleshooting diagnosis solution"
        return self.search(query, top_k)

    def search_by_equipment_type(self, equipment_type: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        return self.search(query, top_k, {"equipment_type": equipment_type})

    def get_procedure_steps(self, procedure_name: str, top_k: int = 5) -> List[Dict[str, Any]]:
        query = f"{procedure_name} procedure steps instructions method process"
        return self.search(query, top_k)

    def get_safety_information(self, context: str, top_k: int = 3) -> List[Dict[str, Any]]:
        query = f"{context} safety precautions warning danger hazard protection"
        return self.search(query, top_k)

    def get_specifications(self, equipment_name: str, spec_type: str, top_k: int = 3) -> List[Dict[str, Any]]:
        query = f"{equipment_name} {spec_type} specification limits range parameters"
        return self.search(query, top_k)

    def get_tool_info(self) -> Dict[str, Any]:
        try:
            metadata_path = self.vector_store_dir / "processing_metadata.json"
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    processing_metadata = json.load(f)
            else:
                processing_metadata = {}

            collection_info = self.vector_store._collection.count()

            return {
                "tool_name": "Manual Search Tool",
                "version": "1.0.0",
                "embedding_model": self.embedding_model,
                "vector_store_path": str(self.vector_store_dir),
                "total_documents": collection_info,
                "processing_metadata": processing_metadata,
                "capabilities": [
                    "Semantic search across technical manuals",
                    "Error code lookup",
                    "Equipment-specific search",
                    "Procedure step retrieval",
                    "Safety information search",
                    "Technical specifications lookup"
                ]
            }

        except Exception as e:
            logger.error(f"Error getting tool info: {str(e)}")
            return {"error": str(e)}

# Run interactively
if __name__ == "__main__":
    print("🛠 Manual Search Tool Loaded ✅")
    tool = ManualSearchTool()

    while True:
        print("\nChoose Search Type:")
        print("1. General")
        print("2. Error Code")
        print("3. Procedure")
        print("4. Safety Info")
        print("5. Specification")
        print("6. Exit")
        choice = input("Enter choice (1-6): ").strip()

        if choice == "6":
            print("👋 Exiting...")
            break

        query = input("\n🔍 Enter your query: ").strip()
        if not query:
            print("⚠️ Please enter a valid query.")
            continue

        if choice == "1":
            results = tool.search(query)
        elif choice == "2":
            results = tool.search_by_error_code(query)
        elif choice == "3":
            results = tool.get_procedure_steps(query)
        elif choice == "4":
            results = tool.get_safety_information(query)
        elif choice == "5":
            parts = query.split()
            if len(parts) >= 2:
                equipment = parts[0]
                spec_type = " ".join(parts[1:])
                results = tool.get_specifications(equipment, spec_type)
            else:
                print("⚠️ Please provide equipment and spec type (e.g., 'motor temperature').")
                continue
        else:
            print("❌ Invalid choice.")
            continue

        print("\n📄 Top Results:")
        for i, result in enumerate(results):
            print(f"\nResult {i+1}:")
            print(f"  📘 Source: {result['metadata']['source']} - Page {result['metadata']['page']}")
            print(f"  🔍 Score: {result['relevance_score']:.3f}")
            print(f"  📝 Content: {result['content']}\n")
