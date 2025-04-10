import os
import hashlib
import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import docling
from docling.document_converter import DocumentConverter
import google.generativeai as genai
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

class DocumentProcessor:
    def __init__(self, data_dir: str, db_path: str, embed_model: str = None, chunk_size: int = None, chunk_overlap: int = None, file_types: List[str] = None):
        """
        Initialize the document processor.
        
        Args:
            data_dir: Directory containing documents to process
            db_path: Path to the SQLite database for tracking processed files
            embed_model: Gemini model to use for embeddings
            chunk_size: Size of text chunks for embeddings
            chunk_overlap: Overlap between text chunks
            file_types: List of file extensions to process
        """
        self.data_dir = Path(data_dir)
        self.db_path = db_path
        
        # Get settings from environment variables or use defaults
        self.chunk_size = chunk_size or int(os.environ.get("MAX_CHUNK_SIZE", 1000))
        self.chunk_overlap = chunk_overlap or int(os.environ.get("CHUNK_OVERLAP", 200))
        self.embed_model = embed_model or os.environ.get("EMBEDDING_MODEL", "models/embedding-001")
        
        # Get file types from environment or use defaults
        if file_types:
            self.file_types = file_types
        else:
            env_file_types = os.environ.get("PROCESS_FILE_TYPES", "pdf,docx,xlsx,pptx,txt,html,md")
            self.file_types = [ext.strip().lower() for ext in env_file_types.split(',')]
        
        # Initialize document converter
        self.converter = DocumentConverter()
        
        # Initialize embeddings model
        self.embeddings = GoogleGenerativeAIEmbeddings(model=self.embed_model)
        
        # Initialize vector store
        self.vectorstore = None
        self.initialize_db()
    
    def initialize_db(self):
        """Initialize the SQLite database for tracking processed files."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            absolute_path TEXT UNIQUE,
            filename TEXT,
            sha256_hash TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def is_file_processed(self, file_path: str) -> bool:
        """Check if a file has already been processed by comparing its hash."""
        file_hash = self.calculate_file_hash(file_path)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id FROM processed_files WHERE sha256_hash = ?", 
            (file_hash,)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        return result is not None
    
    def record_processed_file(self, file_path: str):
        """Record a processed file in the database."""
        abs_path = str(Path(file_path).absolute())
        filename = os.path.basename(file_path)
        file_hash = self.calculate_file_hash(file_path)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT OR REPLACE INTO processed_files (absolute_path, filename, sha256_hash) VALUES (?, ?, ?)",
            (abs_path, filename, file_hash)
        )
        
        conn.commit()
        conn.close()
    
    def get_all_documents(self) -> List[str]:
        """Get all documents from the data directory."""
        documents = []
        
        for root, _, files in os.walk(self.data_dir):
            for file in files:
                # Skip hidden files
                if file.startswith('.'):
                    continue
                
                # Check if file extension is in allowed types
                file_extension = os.path.splitext(file)[1].lower().lstrip('.')
                if file_extension not in self.file_types:
                    print(f"Skipping file with unsupported extension: {file}")
                    continue
                    
                file_path = os.path.join(root, file)
                documents.append(file_path)
        
        return documents
    
    def process_document(self, file_path: str) -> Tuple[List[str], Dict[str, Any]]:
        """Process a single document with Docling and chunk it."""
        try:
            # Convert document using Docling
            result = self.converter.convert(file_path)
            
            # Extract text content
            if result.document:
                text = result.document.export_to_markdown()
                
                # Create chunks
                chunks = []
                for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
                    chunk = text[i:i + self.chunk_size]
                    if len(chunk) > 100:  # Skip very small chunks
                        chunks.append(chunk)
                
                # Create metadata
                metadata = {
                    "source": file_path,
                    "filename": os.path.basename(file_path),
                    "document_type": result.document.document_type,
                }
                
                return chunks, metadata
            else:
                print(f"Warning: Could not extract document from {file_path}")
                return [], {}
                
        except Exception as e:
            print(f"Error processing document {file_path}: {e}")
            return [], {}
    
    def process_all_documents(self):
        """Process all documents in the data directory and create embeddings."""
        documents = self.get_all_documents()
        
        all_chunks = []
        all_metadatas = []
        
        for doc_path in documents:
            if self.is_file_processed(doc_path):
                print(f"Skipping already processed document: {doc_path}")
                continue
                
            print(f"Processing document: {doc_path}")
            chunks, metadata = self.process_document(doc_path)
            
            if chunks:
                # Add document metadata to each chunk
                chunk_metadatas = [{**metadata, "chunk_index": i} for i in range(len(chunks))]
                
                all_chunks.extend(chunks)
                all_metadatas.extend(chunk_metadatas)
                
                # Record this document as processed
                self.record_processed_file(doc_path)
        
        if all_chunks:
            # Create or update vector store
            if self.vectorstore:
                self.vectorstore.add_texts(all_chunks, all_metadatas)
            else:
                self.vectorstore = Chroma.from_texts(
                    texts=all_chunks,
                    embedding=self.embeddings,
                    metadatas=all_metadatas,
                    persist_directory="./chroma_db"
                )
                self.vectorstore.persist()
            
            print(f"Added {len(all_chunks)} chunks to the vector store")
        else:
            print("No new documents to process")
            
    def get_vectorstore(self):
        """Get the current vector store or load it if not initialized."""
        if not self.vectorstore:
            self.vectorstore = Chroma(
                embedding_function=self.embeddings,
                persist_directory="./chroma_db"
            )
        return self.vectorstore 