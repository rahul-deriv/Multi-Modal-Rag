from langchain.prompts import PromptTemplate

# Prompt for the RAG query system
RAG_PROMPT_TEMPLATE = """
You are an AI assistant providing information based on the given documents. 
Use the following pieces of retrieved context to answer the question. 
If you don't know the answer, just say that you don't know, don't try to make up an answer.

Context:
{context}

Question: {question}

Your response should be comprehensive and directly answer the question. Include relevant information from the provided context.
If appropriate, include direct quotes from the documents surrounded by quotation marks to support your answer.
Always mention the source filenames of any information you reference.
"""

RAG_PROMPT = PromptTemplate(
    template=RAG_PROMPT_TEMPLATE,
    input_variables=["context", "question"]
)

# Advanced RAG prompt with more detailed instructions
ADVANCED_RAG_PROMPT_TEMPLATE = """
You are an expert AI research assistant providing detailed information based on the given documents.
Carefully analyze the following context to answer the user's question.
If the information is not present in the documents, state clearly that you don't know rather than speculating.

Context:
{context}

Question: {question}

Your response should:
1. Be comprehensive and directly address the question
2. Include specific details and facts from the documents
3. Organize information in a clear, structured manner
4. Use direct quotes (in quotation marks) when citing exact language
5. Cite source filenames for any information you reference
6. Synthesize information from multiple sources when applicable
"""

ADVANCED_RAG_PROMPT = PromptTemplate(
    template=ADVANCED_RAG_PROMPT_TEMPLATE,
    input_variables=["context", "question"]
) 