import os
from typing import List, Dict, Any, Optional

import google.generativeai as genai
from langchain.chains import RetrievalQA
from langchain_google_genai import ChatGoogleGenerativeAI
from prompts import RAG_PROMPT, ADVANCED_RAG_PROMPT

class RAGQueryEngine:
    def __init__(self, vectorstore, model_name: str = None, api_key: Optional[str] = None, temperature: float = 0.2, use_advanced_prompt: bool = False):
        """
        Initialize the RAG query engine.
        
        Args:
            vectorstore: Vector store containing document embeddings
            model_name: Gemini model to use for generation
            api_key: Google API key (defaults to GOOGLE_API_KEY environment variable)
            temperature: Temperature for generation (0-1)
            use_advanced_prompt: Whether to use the advanced prompt template
        """
        self.vectorstore = vectorstore
        self.use_advanced_prompt = use_advanced_prompt
        
        # Set API key if provided
        if api_key:
            genai.configure(api_key=api_key)
        
        # Get model name from environment variable or use default
        self.model_name = model_name or os.environ.get("QUERY_MODEL", "gemini-1.5-pro")
        
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            temperature=temperature,
            convert_system_message_to_human=True
        )
        
        # Create retriever
        self.retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        )
        
        # Set up the QA chain with custom prompt
        self.qa_chain = self._setup_qa_chain()
    
    def _setup_qa_chain(self):
        """Set up the QA chain with a custom prompt."""
        # Choose between regular and advanced prompt
        prompt = ADVANCED_RAG_PROMPT if self.use_advanced_prompt else RAG_PROMPT
        
        return RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt}
        )
    
    def query(self, question: str) -> Dict[str, Any]:
        """
        Query the RAG system.
        
        Args:
            question: The user's question
            
        Returns:
            Dict containing the answer and source documents
        """
        result = self.qa_chain({"query": question})
        
        # Format sources for easy reading
        sources = []
        for doc in result["source_documents"]:
            source = {
                "content": doc.page_content[:150] + "...",
                "filename": doc.metadata.get("filename", "Unknown"),
                "source": doc.metadata.get("source", "Unknown")
            }
            sources.append(source)
        
        return {
            "answer": result["result"],
            "sources": sources
        }
    
    def get_document_info(self) -> Dict[str, Any]:
        """Get information about the documents in the vector store."""
        # This is an approximation as we can't directly count documents
        # in Chroma without custom collection handling
        try:
            collection_info = self.vectorstore._collection.count()
            return {
                "total_chunks": collection_info,
                "status": "Ready for queries"
            }
        except Exception as e:
            return {
                "status": f"Error retrieving collection info: {e}"
            } 