from datetime import datetime
import os
import json
import numpy as np
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
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.readers.file.docs import PDFReader
from sklearn.metrics.pairwise import cosine_similarity

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams


class CustomDirectoryReader(SimpleDirectoryReader):
    def __init__(self, return_full_document=False, **kwargs):
        super().__init__(**kwargs)
        self.return_full_document = return_full_document
        self.file_extractor[".pdf"] = PDFReader(return_full_document=self.return_full_document)


class DocumentProcessor:
    def __init__(
            self,
            anthropic_api_key: str,
            model_name: str = "claude-3-5-sonnet-20241022",
            persist_dir: str = "./storage",
            embedding_model_name: str = "BAAI/bge-small-en-v1.5",
            qdrant_location: str = ":memory:",
            collection_name: str = "documents",
            chunk_size: int = 1024,
            chunk_overlap: int = 20
    ):
        self.anthropic_api_key = anthropic_api_key
        self.model_name = model_name
        self.persist_dir = persist_dir

        # Initialize components
        self.llm = Anthropic(model=model_name, api_key=anthropic_api_key, max_tokens=8000)
        self.embed_model = HuggingFaceEmbedding(model_name=embedding_model_name)

        # Initialize Qdrant
        self.qdrant = QdrantClient(location=qdrant_location)
        self.collection_name = collection_name

        # Create collection if it doesn't exist
        self.qdrant.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=384,  # BGE-small dimension
                distance=Distance.COSINE
            )
        )

        # Configure node parser
        self.node_parser = SimpleNodeParser.from_defaults(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        # Initialize state
        self.document_summaries = {}
        self.document_hierarchy = {}

    def load_doc(self, doc_path: str) -> Document:
        reader = PDFReader(return_full_document=True)
        doc = reader.load_data(Path(doc_path))

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

        except Exception as e:
            print(f"Error processing document {doc.metadata.get('file_path')}: {str(e)}")

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
                        id=hash(f"{doc.doc_id}_node_{node_idx}"),
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
            similarity_threshold: float = 0.7,
            include_hierarchy: bool = True,
            limit: int = 10,
            context_window: int = 1  # Количество соседних нодов для контекста
    ) -> Dict[str, Any]:
        """Query using Qdrant vector search with node context"""
        try:
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
                    prev_id = hash(f"{doc_id}_node_{i}")
                    prev_nodes = self.qdrant.retrieve(
                        collection_name=self.collection_name,
                        ids=[prev_id]
                    )
                    if prev_nodes:
                        context_nodes.insert(0, prev_nodes[0].payload["text"])

                # Get next nodes
                total_nodes = node_info["total_nodes"]
                for i in range(node_idx + 1, min(total_nodes, node_idx + context_window + 1)):
                    next_id = hash(f"{doc_id}_node_{i}")
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
