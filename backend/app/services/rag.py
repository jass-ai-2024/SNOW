import logging
import traceback
import uuid
from datetime import datetime
import json
from typing import List, Optional, Dict, Any
from pathlib import Path

from llama_index.core import (
    Document,
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    Settings,
    SimpleDirectoryReader
)
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core.schema import RelatedNodeInfo, NodeRelationship, TextNode
from llama_index.llms.anthropic import Anthropic
from llama_index.embeddings.text_embeddings_inference import TextEmbeddingsInference
from llama_index.readers.file.docs import PDFReader
from llama_index.readers.file import MarkdownReader
from llama_index.core import SimpleDirectoryReader

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams

from app.core.config import settings


logger = logging.getLogger(__name__)


import hashlib

def stable_hash(text: str) -> int:
    # Берем первые 8 байт MD5 хеша
    hash_bytes = hashlib.md5(text.encode('utf-8')).digest()[:8]
    return int.from_bytes(hash_bytes, byteorder='big')


class CustomDirectoryReader(SimpleDirectoryReader):
    def __init__(self, return_full_document=False, **kwargs):
        super().__init__(**kwargs)
        self.return_full_document = return_full_document
        self.file_extractor[".pdf"] = PDFReader(return_full_document=self.return_full_document)


class DocumentProcessor:
    def __init__(
            self,
            model_name: str = "claude-3-5-sonnet-20241022",
            persist_dir: str = "./storage",
            embedding_model_name: str = "bge-small-en-v1.5",
            qdrant_location: str = "http://31.31.201.198:6333",
            collection_name: str = "documents",
            chunk_size: int = 1024,
            chunk_overlap: int = 20,
            state_file: str = "document_state.json",
    ):
        self.model_name = model_name
        self.persist_dir = persist_dir
        self.state_file = Path(persist_dir) / state_file

        # Initialize components
        self.llm = Anthropic(
            model=model_name,
            api_key=settings.ANTHROPIC_API_KEY,
            max_tokens=8000
        )
        self.embed_model = TextEmbeddingsInference(
            model_name=embedding_model_name,
            base_url=settings.TEI_BASE_URL
        )

        # Initialize Qdrant
        self.qdrant = QdrantClient(location=qdrant_location)
        self.collection_name = collection_name

        try:
            self.qdrant.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=384,  # BGE-small dimension
                    distance=Distance.COSINE
                )
            )
        except Exception as e:
            pass

        # Configure node parser
        self.node_parser = SimpleNodeParser.from_defaults(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        self.load_state()

    def load_state(self) -> None:
        """Load document state from file"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.document_summaries = state.get('summaries', {})
                    self.document_hierarchy = state.get('hierarchy', {})
            else:
                self.document_summaries = {}
                self.document_hierarchy = {}
        except Exception as e:
            print(f"Error loading state: {str(e)}")
            self.document_summaries = {}
            self.document_hierarchy = {}

    def save_state(self) -> None:
        """Save current document state to file"""
        try:
            state = {
                'summaries': self.document_summaries,
                'hierarchy': self.document_hierarchy,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Error saving state: {str(e)}")

    def load_doc(self, doc_path: str) -> Document:
        reader = SimpleDirectoryReader(
            input_files=[Path(doc_path)]
        )
        doc = reader.load_data()[0]

        try:
            file_path = doc.metadata.get("file_name", "")
            doc_id = Path(file_path).stem

            # Generate summary once and store it
            if doc_id not in self.document_summaries:
                self.document_summaries[doc_id] = self.generate_document_summary(doc)
            summary = self.document_summaries[doc_id]

            document = Document(
                text=doc.get_content(),
                doc_id=doc_id,
                metadata={
                    "file_name": doc.metadata.get("file_name", ""),
                    "file_path": file_path,
                    "file_type": doc.metadata.get("file_type", ""),
                    "creation_date": doc.metadata.get("creation_date", ""),
                    "last_modified_date": doc.metadata.get("last_modified_date", ""),
                    "doc_type": "research_paper",
                    "processed_date": datetime.now().isoformat(),
                    "doc_id": doc_id,
                    "summary": summary,
                    "hierarchy": {
                        "title": "",
                        "summary": "",
                        "parent_id": None,
                        "children": [],
                        "level": 0,
                        "relationships": [],
                        "relationship_type": "",
                        "key_concepts": []
                    }
                }
            )

        except Exception as e:
            print(f"Error processing document {doc.metadata.get('file_path')}: {str(e)}")
            raise

        return document

    def load_documents(self, directory_path: str) -> List[Document]:
        """Load documents using CustomDirectoryReader"""
        try:
            reader = CustomDirectoryReader(
                input_dir=directory_path,
                return_full_document=True,
                recursive=True,
                filename_as_id=True,
                required_exts=[".pdf", ".txt", ".md", ".doc", ".docx"]
            )

            raw_documents = reader.load_data()
            print(f"Found {len(raw_documents)} documents in {directory_path}")

            documents = []
            for doc in raw_documents:
                try:
                    file_path = doc.metadata.get("file_path", "")
                    doc_id = Path(file_path).stem

                    # Generate summary once and store it
                    summary = self.generate_document_summary(doc)
                    self.document_summaries[doc_id] = summary

                    document = Document(
                        text=doc.get_content(),
                        metadata={
                            "file_name": doc.metadata.get("file_name", ""),
                            "file_path": file_path,
                            "file_type": doc.metadata.get("file_type", ""),
                            "creation_date": doc.metadata.get("creation_date", ""),
                            "last_modified_date": doc.metadata.get("last_modified_date", ""),
                            "doc_type": "research_paper",
                            "processed_date": datetime.now().isoformat(),
                            "doc_id": doc_id,
                            "summary": summary,
                            "hierarchy": {
                                "title": "",
                                "summary": "",
                                "parent_id": None,
                                "children": [],
                                "level": 0,
                                "relationships": [],
                                "relationship_type": "",
                                "key_concepts": []
                            }
                        },
                        doc_id=doc_id
                    )
                    documents.append(document)

                except Exception as e:
                    print(f"Error processing document {doc.metadata.get('file_path')}: {str(e)}")
                    continue

            return documents

        except Exception as e:
            print(f"Error loading documents from {directory_path}: {str(e)}")
            return []

    def get_document_info(self) -> Dict[str, Any]:
        """Get information about loaded documents"""
        try:
            search_results = self.qdrant.scroll(
                collection_name=self.collection_name,
                limit=100  # Adjust based on your needs
            )

            docs_info = {}
            for result in search_results[0]:  # [0] contains points, [1] contains next_page_offset
                doc_id = result.payload.get("doc_id")
                if doc_id:
                    docs_info[doc_id] = {
                        "metadata": result.payload.get("metadata", {}),
                        "has_embedding": True,
                        "text_length": len(result.payload.get("text", "")),
                        "hierarchy": result.payload.get("hierarchy", {}),
                        "summary": result.payload.get("summary", "")
                    }

            return {
                "total_documents": len(docs_info),
                "documents": docs_info,
                "index_info": {
                    "has_embeddings": True,
                    "storage_path": self.persist_dir
                }
            }
        except Exception as e:
            print(f"Error getting document info: {str(e)}")
            return {"error": str(e)}

    def generate_document_summary(self, document: Document) -> str:
        """Generate a summary for a document"""
        prompt = f"""Please provide a concise summary of this document, focusing on:
        1. Main topic and key points in two sentences
        2. Any hierarchical relationships or subtopics
        3. Connections to other potential topics

        Document content:
        {document.get_content()[:2000]}...
        """
        response = self.llm.complete(prompt)
        return response.text

    def analyze_hierarchy(self, documents: List[Document]) -> Dict[str, Any]:
        """Analyze documents to determine hierarchical relationships"""
        try:
            doc_summaries = {}

            print("Generating document summaries...")
            for doc in documents:
                doc_id = doc.doc_id.split('/')[-1]
                content_preview = doc.get_content()[:2000]
                summary = self.document_summaries.get(doc_id, self.generate_document_summary(doc))
                doc_summaries[doc_id] = {
                    'preview': content_preview,
                    'summary': summary,
                    'id': doc_id
                }

            hierarchy_prompt = f"""You are a document analysis expert. Create a hierarchical structure for these documents.

            Documents to analyze:
            {json.dumps({k: {'summary': v['summary']} for k, v in doc_summaries.items()}, indent=2)}

            IMPORTANT: Respond ONLY with a valid JSON object. Do not include any explanations or additional text.
            The JSON should follow this exact structure for each document:
            {{
                "doc_id": {{
                    "title": "clear title",
                    "summary": "brief summary",
                    "parent_id": "id of parent document or null if root",
                    "children": ["child_doc_ids"],
                    "level": 0,
                    "relationships": ["related_doc_ids"],
                    "relationship_type": "parent/child/sibling/related",
                    "key_concepts": ["main concepts"]
                }}
            }}
            """

            response = self.llm.complete(hierarchy_prompt)

            try:
                text = response.text.strip()
                start = text.find('{')
                end = text.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = text[start:end]
                    hierarchy = json.loads(json_str)

                    normalized_hierarchy = {}
                    for doc_id, info in hierarchy.items():
                        normalized_info = {
                            "title": info.get("title", ""),
                            "summary": info.get("summary", ""),
                            "parent_id": info.get("parent_id"),
                            "children": [str(child) for child in info.get("children", []) if child],
                            "level": info.get("level", 0),
                            "relationships": [str(rel) for rel in info.get("relationships", []) if rel],
                            "relationship_type": info.get("relationship_type", "root"),
                            "key_concepts": info.get("key_concepts", [])
                        }
                        normalized_hierarchy[str(doc_id)] = normalized_info

                    self._validate_and_fix_relationships(normalized_hierarchy)

                    print("\nSuccessfully created hierarchy:")
                    print(json.dumps(normalized_hierarchy, indent=2))
                    return normalized_hierarchy
                else:
                    print("No valid JSON found in response")
                    return {}

            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {str(e)}")
                print("Raw response:", response.text)
                return {}

        except Exception as e:
            print(f"Error in analyze_hierarchy: {str(e)}")
            return {}

    def analyze_single_document_hierarchy(self, document: Document) -> Dict[str, Any]:
        """Analyze hierarchical relationships for a single new document"""
        try:
            doc_id = document.doc_id
            summary = self.document_summaries.get(doc_id, self.generate_document_summary(document))
            self.save_state()

            # Prepare context of existing documents and the new one
            existing_docs = {
                doc_id: {
                    'summary': summary,
                    'is_new': True
                }
            }

            # Add existing documents for context
            for existing_id, existing_summary in self.document_summaries.items():
                if existing_id != doc_id:
                    existing_docs[existing_id] = {
                        'summary': existing_summary,
                        'is_new': False
                    }

            hierarchy_prompt = f"""You are a document analysis expert. Analyze how this new document fits into the existing document hierarchy.

            New document summary:
            {summary}

            Existing document summaries:
            {json.dumps({k: v['summary'] for k, v in existing_docs.items() if not v['is_new']}, indent=2)}

            Existing hierarchy:
            {json.dumps(self.document_hierarchy, indent=2)}

            IMPORTANT: Respond ONLY with a valid JSON object for the new document. Do not include any explanations.
            The JSON should follow this structure:
            {{
                "{doc_id}": {{
                    "title": "clear title",
                    "summary": "brief summary",
                    "parent_id": "id of most related parent document or null if root",
                    "children": ["child_doc_ids"],
                    "level": 0,
                    "relationships": ["related_doc_ids"],
                    "relationship_type": "parent/child/sibling/related",
                    "key_concepts": ["main concepts"],
                    "similarity_scores": {{"doc_id": score}} // similarity to other docs
                }}
            }}
            """

            response = self.llm.complete(hierarchy_prompt)
            print(doc_id, response.text)
            try:
                text = response.text.strip()
                start = text.find('{')
                end = text.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = text[start:end]
                    new_hierarchy = json.loads(json_str)

                    if len(new_hierarchy.keys()) == 1:
                        new_hierarchy = list(new_hierarchy.values())[0]

                    # Normalize the hierarchy entry
                    normalized_entry = {
                        "title": new_hierarchy.get("title", ""),
                        "summary": new_hierarchy.get("summary", ""),
                        "parent_id": new_hierarchy.get("parent_id"),
                        "children": [str(child) for child in new_hierarchy.get("children", []) if child],
                        "level": new_hierarchy.get("level", 0),
                        "relationships": [str(rel) for rel in new_hierarchy.get("relationships", []) if rel],
                        "relationship_type": new_hierarchy.get("relationship_type", "root"),
                        "key_concepts": new_hierarchy.get("key_concepts", []),
                        "similarity_scores": new_hierarchy.get("similarity_scores", {})
                    }

                    return {doc_id: normalized_entry}
                else:
                    print("No valid JSON found in response")
                    return {}

            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {str(e)}")
                print("Raw response:", response.text)
                return {}

        except Exception as e:
            print(f"Error in analyze_single_document_hierarchy: {str(e)}")
            print(traceback.format_exc())
            return {}

    def update_hierarchy_with_document(self, doc_id: str, new_hierarchy: Dict[str, Any]) -> None:
        """Update existing hierarchy with a new document's relationships"""
        try:
            if not new_hierarchy or doc_id not in new_hierarchy:
                return

            doc_info = new_hierarchy[doc_id]

            # Update existing relationships based on similarity scores
            similarity_scores = doc_info.get("similarity_scores", {})
            threshold = 0.7  # Можно сделать настраиваемым параметром

            related_docs = [
                rel_id for rel_id, score in similarity_scores.items()
                if score >= threshold and rel_id in self.document_hierarchy
            ]

            # Add new relationships to existing documents
            for rel_id in related_docs:
                if rel_id not in doc_info["relationships"]:
                    doc_info["relationships"].append(rel_id)

                # Update the related document's relationships
                if rel_id in self.document_hierarchy:
                    rel_doc = self.document_hierarchy[rel_id]
                    if doc_id not in rel_doc["relationships"]:
                        rel_doc["relationships"].append(doc_id)

            # Handle parent-child relationships
            parent_id = doc_info["parent_id"]
            if parent_id and parent_id in self.document_hierarchy:
                parent = self.document_hierarchy[parent_id]
                if doc_id not in parent["children"]:
                    parent["children"].append(doc_id)
                doc_info["level"] = parent["level"] + 1
            else:
                doc_info["parent_id"] = None
                doc_info["level"] = 0

            # Update children's parent references if any
            for child_id in doc_info["children"]:
                if child_id in self.document_hierarchy:
                    child = self.document_hierarchy[child_id]
                    child["parent_id"] = doc_id
                    child["level"] = doc_info["level"] + 1

            # Add the new document to the hierarchy
            self.document_hierarchy[doc_id] = doc_info

            print(f"Successfully updated hierarchy with document: {doc_id}")

        except Exception as e:
            print(f"Error updating hierarchy: {str(e)}")

    def add_document(self, doc_path: str) -> Optional[Document]:
        """Add a single document to the system"""
        try:
            # Load document
            document = self.load_doc(doc_path)
            if not document:
                return None

            doc_id = document.doc_id

            if doc_id not in self.document_summaries:
                # Generate and store summary
                self.document_summaries[doc_id] = self.generate_document_summary(document)

            summary = self.document_summaries[doc_id]

            # Analyze and update hierarchy for the new document
            new_hierarchy = self.analyze_single_document_hierarchy(document)
            if new_hierarchy:
                self.update_hierarchy_with_document(doc_id, new_hierarchy)

            # Process document nodes
            nodes = self.node_parser.get_nodes_from_documents([document])
            points = []

            for node_idx, node in enumerate(nodes):
                embedding = self.embed_model.get_text_embedding(node.text)

                # Create relationships between nodes
                node_relationships = []
                if node_idx > 0:
                    node_relationships.append({
                        "type": "previous",
                        "node_id": f"{doc_id}_node_{node_idx - 1}"
                    })
                if node_idx < len(nodes) - 1:
                    node_relationships.append({
                        "type": "next",
                        "node_id": f"{doc_id}_node_{node_idx + 1}"
                    })

                point = models.PointStruct(
                    id=stable_hash(f"{doc_id}_node_{node_idx}"),
                    vector=embedding,
                    payload={
                        'doc_id': doc_id,
                        'node_id': f"{doc_id}_node_{node_idx}",
                        'text': node.text,
                        'metadata': {
                            **document.metadata,
                            'node_info': {
                                'index': node_idx,
                                'total_nodes': len(nodes),
                                'relationships': node_relationships,
                                'start_char_idx': node.start_char_idx,
                                'end_char_idx': node.end_char_idx
                            }
                        },
                        'hierarchy': self.document_hierarchy.get(doc_id, {}),
                        'summary': summary
                    }
                )
                points.append(point)

            # Upload points
            result = self.qdrant.upsert(
                collection_name=self.collection_name,
                points=points
            )

            print(result)

            # Save updated state
            self.save_state()

            print(f"Successfully added document: {doc_id}")
            return document

        except Exception as e:
            print(f"Error adding document: {str(e)}")
            print(traceback.format_exc())
            return None

    def _validate_and_fix_relationships(self, hierarchy: Dict[str, Any]) -> None:
        """Validate and fix hierarchical relationships"""
        for doc_id, info in hierarchy.items():
            parent_id = info.get("parent_id")
            if parent_id:
                if parent_id in hierarchy:
                    parent = hierarchy[parent_id]
                    if doc_id not in parent["children"]:
                        parent["children"].append(doc_id)
                    info["level"] = parent["level"] + 1
                else:
                    info["parent_id"] = None
                    info["level"] = 0

        for doc_id, info in hierarchy.items():
            relationships = info.get("relationships", [])
            valid_relationships = []
            for rel_id in relationships:
                if rel_id in hierarchy and rel_id != doc_id:
                    valid_relationships.append(rel_id)
                    rel_info = hierarchy[rel_id]
                    if doc_id not in rel_info.get("relationships", []):
                        rel_info.setdefault("relationships", []).append(doc_id)
            info["relationships"] = valid_relationships

    def process_documents(self, documents: List[Document]) -> None:
        """Process documents and create node vectors in Qdrant"""
        try:
            print("Analyzing document hierarchies...")
            self.document_hierarchy = self.analyze_hierarchy(documents)

            print("Creating document nodes and vectors...")
            points = []

            for doc in documents:
                # Parse document into nodes
                nodes = self.node_parser.get_nodes_from_documents([doc])

                for node_idx, node in enumerate(nodes):
                    # Generate embedding for node
                    embedding = self.embed_model.get_text_embedding(node.text)

                    # Create relationships between nodes
                    node_relationships = []
                    if node_idx > 0:
                        node_relationships.append({
                            "type": "previous",
                            "node_id": f"{doc.doc_id}_node_{node_idx - 1}"
                        })
                    if node_idx < len(nodes) - 1:
                        node_relationships.append({
                            "type": "next",
                            "node_id": f"{doc.doc_id}_node_{node_idx + 1}"
                        })

                    # Create point for Qdrant
                    point = models.PointStruct(
                        id=stable_hash(f"{doc.doc_id}_node_{node_idx}"),
                        vector=embedding,
                        payload={
                            'doc_id': doc.doc_id,
                            'node_id': f"{doc.doc_id}_node_{node_idx}",
                            'text': node.text,
                            'metadata': {
                                **doc.metadata,
                                'node_info': {
                                    'index': node_idx,
                                    'total_nodes': len(nodes),
                                    'relationships': node_relationships,
                                    'start_char_idx': node.start_char_idx,
                                    'end_char_idx': node.end_char_idx
                                }
                            },
                            'hierarchy': self.document_hierarchy.get(doc.doc_id.split('/')[-1], {}),
                            'summary': self.document_summaries.get(doc.doc_id, '')
                        }
                    )
                    points.append(point)

            # Upload in batches
            BATCH_SIZE = 100
            for i in range(0, len(points), BATCH_SIZE):
                batch = points[i:i + BATCH_SIZE]
                self.qdrant.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )

            print(f"Uploaded {len(points)} nodes to Qdrant")

        except Exception as e:
            print(f"Error processing documents: {str(e)}")
            raise

    def query(
            self,
            query_text: str,
            similarity_threshold: float = 0.0,
            include_hierarchy: bool = True,
            limit: int = 10,
            context_window: int = 1  # Количество соседних нодов для контекста
    ) -> Dict[str, Any]:
        """Query using Qdrant vector search with node context"""
        try:
            logger.error(query_text)
            query_embedding = self.embed_model.get_text_embedding(query_text)

            # Search in Qdrant
            search_results = self.qdrant.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=similarity_threshold
            )

            # Process results and get context
            results = []
            context_texts = []

            for result in search_results:
                node_info = result.payload["metadata"]["node_info"]
                doc_id = result.payload["doc_id"]
                node_idx = node_info["index"]

                # Get surrounding context nodes
                context_nodes = [result.payload["text"]]  # Start with current node

                # Get previous nodes
                for i in range(max(0, node_idx - context_window), node_idx):
                    prev_id = stable_hash(f"{doc_id}_node_{i}")
                    prev_nodes = self.qdrant.retrieve(
                        collection_name=self.collection_name,
                        ids=[prev_id]
                    )
                    if prev_nodes:
                        context_nodes.insert(0, prev_nodes[0].payload["text"])

                # Get next nodes
                total_nodes = node_info["total_nodes"]
                for i in range(node_idx + 1, min(total_nodes, node_idx + context_window + 1)):
                    next_id = stable_hash(f"{doc_id}_node_{i}")
                    next_nodes = self.qdrant.retrieve(
                        collection_name=self.collection_name,
                        ids=[next_id]
                    )
                    if next_nodes:
                        context_nodes.append(next_nodes[0].payload["text"])

                context = "\n".join(context_nodes)

                result_dict = {
                    "text": result.payload["text"],
                    "context": context,
                    "similarity": result.score,
                    "metadata": result.payload["metadata"],
                    "node_info": node_info
                }

                if include_hierarchy:
                    result_dict["hierarchy_info"] = result.payload["hierarchy"]

                results.append(result_dict)
                context_texts.append(context)

            # Generate response using context from nodes
            prompt = f"""Based on the following context, answer the question: {query_text}

            Context:
            {' '.join(context_texts)}
            """
            response = self.llm.complete(prompt)

            return {
                "response": str(response.text),
                "sources": results,
                "total_sources": len(results)
            }

        except Exception as e:
            logger.exception(e)
            print(f"Error in query processing: {str(e)}")
            return {
                "response": "",
                "sources": [],
                "total_sources": 0
            }

    def process_directory(self, directory_path: str) -> None:
        """Process all documents in a directory"""
        documents = self.load_documents(directory_path)
        if documents:
            self.process_documents(documents)
            print(f"Processed {len(documents)} documents")
        else:
            print("No documents were loaded")

    def get_hierarchy_json(self) -> str:
        """Get the document hierarchy as JSON string"""
        return json.dumps({
            "hierarchy": self.document_hierarchy,
            "summaries": self.document_summaries
        }, indent=2)
