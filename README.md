# Document RAG System

A Retrieval-Augmented Generation (RAG) system for processing and querying documents using [Docling](https://github.com/docling-project/docling) and Google Gemini 2.0.

## Features

- Process documents from nested folder structures
- Support for various document formats (PDF, DOCX, XLSX, HTML, etc.) via Docling
- Generate embeddings using Google Gemini 2.0
- Track processed files to avoid redundant processing
- Interactive query mode for asking questions about your documents
- Flexible file type category system for controlling which file types to process
- Choose between standard and advanced prompt templates for different query needs

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Get a Google API key with access to Gemini models:
   - Visit [Google AI Studio](https://ai.google.dev/)
   - Create an API key

3. Place your documents in the `data/` folder (the system will create this if it doesn't exist)

## Usage

### Process Documents

To process all documents in the data directory:

```bash
python main.py --api-key YOUR_API_KEY
```

Or set your API key as an environment variable:

```bash
export GOOGLE_API_KEY=your_api_key
python main.py
```

### Query the System

After processing, you can query the system in interactive mode:

```bash
python main.py
```

Or make a single query:

```bash
python main.py --query "What is the main topic of these documents?"
```

### File Categories

You can control which file types are processed using the file category system:

```bash
# List all available file categories
python main.py --list-categories

# Process only specific file categories
python main.py --file-categories "text_documents,presentations"
```

Available categories include:
- `text_documents` (pdf, docx, txt, etc.)
- `spreadsheets` (xlsx, csv, etc.)
- `presentations` (pptx, odp)
- `images` (png, jpg, etc.) - requires OCR capability
- `audio` (mp3, wav, etc.) - requires speech-to-text capability
- `video` (mp4, avi, etc.) - requires video transcription capability

### Advanced Prompts

Use the advanced prompt template for more structured responses:

```bash
python main.py --advanced-prompt
```

### Additional Options

```
--data-dir DATA_DIR     Directory containing documents (default: data)
--db-path DB_PATH       Path to SQLite database (default: processed_files.db)
--process               Force processing of all documents
--file-categories       Comma-separated list of file categories to process
--advanced-prompt       Use the advanced prompt template for queries
--list-categories       List all available file categories and exit
```

## How It Works

1. The system scans the `data/` directory for documents
2. Uses Docling to convert and extract content from various document formats
3. Creates text chunks and embeddings with Gemini 2.0
4. Stores embeddings in a Chroma vector database
5. Tracks processed files in a SQLite database using file hashes
6. When queried, retrieves the most relevant document chunks and generates an answer

## File Structure

- `main.py` - Main entry point and CLI interface
- `doc_loader.py` - Document processing logic using Docling
- `query.py` - Query handling with RAG
- `prompts.py` - Prompt templates for different query modes
- `file_config.py` - File type category configurations
- `data/` - Directory for storing documents
- `chroma_db/` - Directory for vector store
- `processed_files.db` - SQLite database tracking processed files 