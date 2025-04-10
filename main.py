import os
import argparse
from typing import Optional, List
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import google.generativeai as genai
from doc_loader import DocumentProcessor
from query import RAGQueryEngine
import file_config

def setup_api_key(api_key: Optional[str] = None) -> bool:
    """Set up the Google API key."""
    # Use provided API key or try to get from environment
    key = api_key or os.environ.get("GOOGLE_API_KEY")
    
    if not key:
        print("ERROR: Google API key is required.")
        print("Either provide it with --api-key or set the GOOGLE_API_KEY environment variable.")
        return False
    
    # Configure genai
    genai.configure(api_key=key)
    return True

def check_and_process_documents(data_dir: str, db_path: str, api_key: Optional[str] = None, file_categories: Optional[List[str]] = None):
    """Check for new documents and process them if found."""
    print(f"Checking for new documents in {data_dir}")
    
    # Create data directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)
    
    # Get settings from environment variables
    embed_model = os.environ.get("EMBEDDING_MODEL", "models/embedding-001")
    chunk_size = int(os.environ.get("MAX_CHUNK_SIZE", 1000))
    chunk_overlap = int(os.environ.get("CHUNK_OVERLAP", 200))
    
    # Get file types based on enabled categories
    file_types = file_config.get_enabled_file_types(file_categories)
    
    # Initialize document processor
    processor = DocumentProcessor(
        data_dir=data_dir,
        db_path=db_path,
        embed_model=embed_model,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        file_types=file_types
    )
    
    # Get all documents and check if any are unprocessed
    documents = processor.get_all_documents()
    unprocessed_docs = [doc for doc in documents if not processor.is_file_processed(doc)]
    
    if unprocessed_docs:
        print(f"Found {len(unprocessed_docs)} new documents to process.")
        print(f"Using embedding model: {embed_model}")
        print(f"Chunk size: {chunk_size}, Overlap: {chunk_overlap}")
        
        # Print enabled categories and file types
        enabled_categories = file_categories or file_config.DEFAULT_ENABLED_CATEGORIES
        print(f"Enabled file categories: {', '.join(enabled_categories)}")
        print(f"Processing file types: {', '.join(file_types)}")
        
        # Process all documents (the method will only process unprocessed ones)
        processor.process_all_documents()
        print("Document processing complete.")
    else:
        print("No new documents found. Using existing document embeddings.")
    
    return processor.get_vectorstore()

def interactive_query_mode(query_engine):
    """Run an interactive query session."""
    print("\n=== RAG Query Mode ===")
    print("Type 'exit' or 'quit' to end the session.")
    
    while True:
        query = input("\nEnter your question: ")
        
        if query.lower() in ['exit', 'quit']:
            break
        
        if not query.strip():
            continue
        
        # Get answer
        result = query_engine.query(query)
        
        # Print answer
        print("\nAnswer:")
        print(result["answer"])
        
        # Print sources
        print("\nSources:")
        for i, source in enumerate(result["sources"], 1):
            print(f"{i}. {source['filename']}")

def main():
    parser = argparse.ArgumentParser(description="Document RAG System")
    
    # Command arguments
    parser.add_argument("--api-key", type=str, help="Google API key (or set GOOGLE_API_KEY environment variable)")
    parser.add_argument("--data-dir", type=str, default="data", help="Directory containing documents (default: data)")
    parser.add_argument("--db-path", type=str, default="processed_files.db", help="Path to SQLite database (default: processed_files.db)")
    parser.add_argument("--process", action="store_true", help="Force processing of all documents")
    parser.add_argument("--query", type=str, help="Query the RAG system and exit")
    parser.add_argument("--advanced-prompt", action="store_true", help="Use the advanced prompt template for queries")
    parser.add_argument("--file-categories", type=str, help="Comma-separated list of file categories to process")
    parser.add_argument("--list-categories", action="store_true", help="List all available file categories and exit")
    
    args = parser.parse_args()
    
    # List available categories if requested
    if args.list_categories:
        print("Available file categories:")
        for category in file_config.get_all_categories():
            extensions = file_config.CATEGORY_MAP[category]
            print(f"  - {category}: {', '.join(extensions)}")
        print(f"\nDefault enabled categories: {', '.join(file_config.DEFAULT_ENABLED_CATEGORIES)}")
        return
    
    # Setup API key
    if not setup_api_key(args.api_key):
        return
    
    # Parse file categories if provided
    file_categories = None
    if args.file_categories:
        file_categories = [cat.strip() for cat in args.file_categories.split(',')]
        
        # Validate categories
        all_categories = file_config.get_all_categories()
        invalid_categories = [cat for cat in file_categories if cat not in all_categories]
        if invalid_categories:
            print(f"Warning: Invalid file categories: {', '.join(invalid_categories)}")
            print(f"Available categories: {', '.join(all_categories)}")
            file_categories = [cat for cat in file_categories if cat in all_categories]
            if not file_categories:
                print("No valid categories provided. Using defaults.")
                file_categories = None
    
    # Check for new documents and process them automatically
    vectorstore = check_and_process_documents(
        args.data_dir, 
        args.db_path, 
        args.api_key,
        file_categories
    )
    
    # Initialize query engine with the selected prompt
    query_engine = RAGQueryEngine(
        vectorstore=vectorstore,
        use_advanced_prompt=args.advanced_prompt
    )
    
    # Show which prompt is being used
    prompt_type = "Advanced" if args.advanced_prompt else "Standard"
    print(f"Using {prompt_type} prompt template for queries.")
    
    # Get document info
    doc_info = query_engine.get_document_info()
    print(f"Document Status: {doc_info['status']}")
    
    if 'total_chunks' in doc_info:
        print(f"Total chunks in vector store: {doc_info['total_chunks']}")
    
    # Handle single query mode
    if args.query:
        result = query_engine.query(args.query)
        print("\nAnswer:")
        print(result["answer"])
        
        print("\nSources:")
        for i, source in enumerate(result["sources"], 1):
            print(f"{i}. {source['filename']}")
    else:
        # Interactive mode
        interactive_query_mode(query_engine)

if __name__ == "__main__":
    main()
