from typing import List
from aiogram.types import Message
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import Document

from ..core import settings
from ..logging import logger


def get_openrouter_llm():
    logger.info("Initializing OpenRouter LLM...")
    llm = ChatOpenAI(
        model=settings.get_model_name(),
        openai_api_key=settings.get_llm_token(),
        openai_api_base="https://openrouter.ai/api/v1"
    )
    logger.info(f"LLM initialized with model: {settings.get_model_name()}")
    return llm


qa_prompt_template = """
Answer ONLY in English.
Use the provided data from these sections to answer the question if possible:
{context}

IMPORTANT: Only answer questions related to cooking, recipes, food preparation, or culinary topics.
If the question is not related to these topics, respond with:
"I can only answer questions related to cooking and culinary topics."

If you are confident the question is about cooking but there is no relevant information in the provided data, answer based on your general knowledge.
Answer format:
1. [item]
 - [Item details]
2. [Next item]

Question: {question}
Answer:
"""

prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=qa_prompt_template
)

from langchain.schema import HumanMessage

async def get_answer(documents: List, message: Message):
    logger.info(f"Received {len(documents)} documents for processing.")

    llm = get_openrouter_llm()

    if not documents:
        logger.warning("Documents list is empty, querying LLM without context.")
        context = ""
        formatted_prompt = prompt.format(context=context, question=message.text)
        try:
            messages = [HumanMessage(content=formatted_prompt)]
            result = await llm.ainvoke(messages)

            logger.info("Query executed successfully without documents.")
            return {
                "result": result.content if hasattr(result, "content") else str(result),
                "source_documents": []
            }
        except Exception as e:
            logger.exception(f"Error running query without documents: {e}")
            raise

    try:
        docs = [Document(page_content=d["text"], metadata=d.get("metadata", {})) for d in documents]
        logger.info(f"Converted to {len(docs)} Document objects.")
    except Exception as e:
        logger.exception(f"Error converting documents: {e}")
        raise

    try:
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        logger.info("HuggingFaceEmbeddings initialized.")
    except Exception as e:
        logger.exception(f"Error initializing embeddings: {e}")
        raise

    try:
        vectorstore = FAISS.from_documents(docs, embeddings)
        logger.info("FAISS vectorstore created successfully.")
    except Exception as e:
        logger.exception(f"Error creating FAISS vectorstore: {e}")
        raise

    try:
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt}
        )
        logger.info("RetrievalQA chain initialized.")
    except Exception as e:
        logger.exception(f"Error initializing QA chain: {e}")
        raise

    logger.info(f"Running query: {message.text}")

    try:
        result = await qa_chain.ainvoke({"query": message.text})
        logger.info("Query executed successfully.")
    except Exception as e:
        logger.exception(f"Error running query: {e}")
        raise

    return result
