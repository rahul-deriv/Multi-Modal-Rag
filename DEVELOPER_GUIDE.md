# Developer Guide: Document RAG System

This guide provides technical details for developers working on or extending the Document RAG System.

## Project Structure

```
.
├── main.py               # Main script, CLI interface, orchestration
├── doc_loader.py         # Document loading, processing (Docling), embedding, and DB tracking
├── query.py              # RAG query engine, interaction with LLM and vector store
├── prompts.py            # Contains prompt templates for the RAG query engine
├── file_config.py        # Defines file type categories and manages allowed file types
├── requirements.txt      # Python dependencies
├── .env.example          # Example environment variables file
├── .env                  # Actual environment variables (ignored by git)
├── data/                 # Directory for source documents (create manually or by script)
├── chroma_db/            # Persistent vector store directory (created by Chroma)
├── processed_files.db    # SQLite database tracking processed files (created by script)
└── README.md             # General user documentation
└── DEVELOPER_GUIDE.md    # This file
```

## Core Components

### 1. `DocumentProcessor` (`doc_loader.py`)

- **Responsibilities:**
    - Scans the `data_dir` for documents.
    - Filters documents based on the `file_types` list provided during initialization (which comes from `file_config.py` via `main.py`).
    - Uses `docling` to convert various file formats (PDF, DOCX, etc.) into markdown text.
    - Checks the `processed_files.db` (SQLite) using SHA-256 hashes to avoid reprocessing unchanged files.
    - Chunks the extracted text based on `MAX_CHUNK_SIZE` and `CHUNK_OVERLAP` (from `.env`).
    - Generates embeddings for text chunks using the specified `EMBEDDING_MODEL` (from `.env`) via `langchain_google_genai.GoogleGenerativeAIEmbeddings`.
    - Adds the chunks and their metadata (source file, document type) to the Chroma vector store (`./chroma_db`).
    - Updates the `processed_files.db` with the hash of newly processed files.
- **Key Methods:**
    - `__init__(...)`: Initializes the processor, takes configuration parameters (including `file_types`).
    - `get_all_documents()`: Finds and filters relevant documents in the data directory based on `self.file_types`.
    - `is_file_processed()`: Checks the SQLite DB for a file's hash.
    - `process_document()`: Converts a single file using Docling and creates text chunks.
    - `process_all_documents()`: Orchestrates the processing of all new/modified documents and updates the vector store.
    - `get_vectorstore()`: Returns the initialized Chroma vector store instance.

### 2. `RAGQueryEngine` (`query.py`)

- **Responsibilities:**
    - Initializes the language model (`langchain_google_genai.ChatGoogleGenerativeAI`) using the `QUERY_MODEL` specified in `.env`.
    - Takes the initialized `vectorstore` (Chroma) as input.
    - Takes a `use_advanced_prompt` boolean flag to determine which prompt template to use.
    - Creates a LangChain retriever from the vector store to find relevant document chunks.
    - Sets up a `RetrievalQA` chain from LangChain.
    - Uses a selected prompt template (either standard or advanced) imported from `prompts.py` to guide the LLM in generating answers based on retrieved context.
    - Provides a `query()` method to handle user questions, retrieve context, and generate answers.
    - Formats the response to include the answer and details about the source documents.
- **Key Methods:**
    - `__init__(...)`: Initializes the query engine, LLM, retriever, and selects the prompt based on `use_advanced_prompt`.
    - `_setup_qa_chain()`: Configures the LangChain `RetrievalQA` chain with the selected prompt.
    - `query()`: Executes the RAG process for a given question.
    - `get_document_info()`: Provides basic information about the vector store (e.g., number of chunks).

### 3. `main.py`

- **Responsibilities:**
    - Parses command-line arguments (`--query`, `--api-key`, `--file-categories`, `--advanced-prompt`, `--list-categories`, etc.).
    - Loads environment variables from the `.env` file using `python-dotenv`.
    - Sets up the Google Generative AI API key.
    - Calls `check_and_process_documents` to automatically scan for and process new/updated documents based on the specified or default file categories (from `file_config.py`). The `--process` flag can be used to force reprocessing of all files.
    - Retrieves the list of enabled file types from `file_config.py` based on command-line arguments or defaults.
    - Initializes the `DocumentProcessor` and `RAGQueryEngine`, passing the appropriate configuration (including the list of file types and the choice of prompt).
    - Handles listing available file categories (`--list-categories`).
    - Runs either the single query mode (`--query`) or the interactive query loop (`interactive_query_mode`).

### 4. `prompts.py`

- **Responsibilities:**
    - Defines different prompt templates for the `RAGQueryEngine` using `langchain.prompts.PromptTemplate`.
    - Exports prompt template instances (e.g., `RAG_PROMPT`, `ADVANCED_RAG_PROMPT`) for use in `query.py`.
    - Centralizes prompt engineering, making it easy to modify or add new prompt strategies.

### 5. `file_config.py`

- **Responsibilities:**
    - Defines categories of file types (e.g., `TEXT_DOCUMENT_TYPES`, `SPREADSHEET_TYPES`).
    - Maps category names to lists of file extensions.
    - Specifies default enabled categories (`DEFAULT_ENABLED_CATEGORIES`).
    - Provides functions (`get_enabled_file_types`, `get_all_categories`) for `main.py` to retrieve the correct list of file extensions based on user input or defaults.
    - Replaces the `.env` variable `PROCESS_FILE_TYPES` for managing supported file types.

## Configuration

Configuration is managed through two primary mechanisms:

1.  **Environment Variables (`.env` file):** Used for secrets and infrastructure settings.
    - `GOOGLE_API_KEY`: **Required**. Your API key for Google Gemini.
    - `EMBEDDING_MODEL`: The embedding model to use during document ingestion (e.g., `models/embedding-001`).
    - `QUERY_MODEL`: The generative model used for answering questions (e.g., `gemini-1.5-pro`).
    - `CHROMA_DB_PATH`: Path to the Chroma vector store directory (defaults to `./chroma_db`).
    - `MAX_CHUNK_SIZE`: Maximum characters per text chunk for embedding.
    - `CHUNK_OVERLAP`: Number of characters to overlap between consecutive chunks.

2.  **File Configuration (`file_config.py`):** Defines supported file types and categories.
    - Edit the lists (e.g., `TEXT_DOCUMENT_TYPES`) to add or remove supported extensions.
    - Modify `DEFAULT_ENABLED_CATEGORIES` to change which types are processed by default.

3.  **Command-Line Arguments (`main.py`):** Allows overriding defaults and controlling behavior at runtime.
    - `--file-categories`: Specify which categories from `file_config.py` to process (e.g., `"text_documents,presentations"`). Overrides defaults.
    - `--list-categories`: Show available categories defined in `file_config.py`.
    - `--advanced-prompt`: Use the `ADVANCED_RAG_PROMPT` from `prompts.py` instead of the standard one.
    - `--process`: Force reprocessing of all files in the specified categories, ignoring the SQLite tracking database.

## Dependencies

Key libraries used:

- `docling`: For converting various document formats.
- `google-generativeai`: Google's official Python client for Gemini.
- `langchain`, `langchain-google-genai`, `langchain-community`: Framework for building LLM applications (retrieval, chains, prompts).
- `chromadb`: Vector store for embeddings.
- `python-dotenv`: For loading environment variables from `.env`.
- `sqlite3`: (Built-in) For the processed file tracking database.
- `hashlib`: (Built-in) For generating file hashes.

Install all dependencies using `pip install -r requirements.txt`.

## Extending the System

- **Adding New Document Types:** If Docling supports the format, add the file extension to the appropriate list (e.g., `TEXT_DOCUMENT_TYPES`) in `file_config.py`. If a new category is needed, define it and add it to `CATEGORY_MAP`.
- **Changing the Vector Store:** Modify `doc_loader.py` and `query.py` to use a different LangChain-compatible vector store.
- **Modifying Prompts:** Edit the prompt templates defined in `prompts.py`.
- **Adding New Prompts:** Define a new `PromptTemplate` in `prompts.py` and modify `RAGQueryEngine` and `main.py` to allow selecting it (e.g., via a new command-line argument).
- **Adjusting Chunking Strategy:** Change `MAX_CHUNK_SIZE` and `CHUNK_OVERLAP` in `.env` or modify the chunking logic in `DocumentProcessor.process_document`.
- **Using Different Models:** Update `EMBEDDING_MODEL` and `QUERY_MODEL` in `.env` to compatible model names provided by Google Generative AI. 