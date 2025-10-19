import json
import os
import sys
import boto3
import streamlit as st

## We will be suing Titan Embeddings Model To generate Embedding

from langchain_community.embeddings import BedrockEmbeddings
from langchain.llms.bedrock import Bedrock

## Data Ingestion
import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFDirectoryLoader

# Vector Embedding And Vector Store

from langchain.vectorstores import FAISS

## LLm Models
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

## Bedrock Clients
bedrock = boto3.client(service_name="bedrock-runtime")
bedrock_embeddings = BedrockEmbeddings(model_id="amazon.titan-embed-text-v1", client=bedrock)

# Claude Sonnet model id for Bedrock. Override via env if needed.
CLAUDE_SONNET_MODEL_ID = os.environ.get(
    "BEDROCK_CLAUDE_SONNET_MODEL_ID",
    # Default to Claude Sonnet 4.5; update to your regional variant if necessary
    "anthropic.claude-4.5-sonnet-v1:0",
)


## Data ingestion
def data_ingestion():
    loader=PyPDFDirectoryLoader("data")
    documents=loader.load()

    # - in our testing Character split works better with this PDF data set
    text_splitter=RecursiveCharacterTextSplitter(chunk_size=10000,
                                                 chunk_overlap=1000)
    
    docs=text_splitter.split_documents(documents)
    return docs

## Vector Embedding and vector store

def get_vector_store(docs):
    vectorstore_faiss = FAISS.from_documents(
        docs,
        bedrock_embeddings,
    )
    vectorstore_faiss.save_local("faiss_index")

def get_claude_llm():
    ## Create the Anthropic Claude Sonnet model (via Bedrock)
    llm = Bedrock(model_id=CLAUDE_SONNET_MODEL_ID, client=bedrock)
    return llm

def get_llama2_llm():
    ## Create the Llama 2 model (via Bedrock)
    llm = Bedrock(model_id="meta.llama2-70b-chat-v1", client=bedrock, model_kwargs={"max_gen_len": 512})
    return llm

prompt_template = """
Human: Use the following pieces of context to provide a concise, accurate answer
to the user's question. Aim for at least 250 words and include clear, practical
details. If you don't know the answer, say you don't know.
<context>
{context}
</context>

Question: {question}

Assistant:"""

PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

# Agent-role specific prompts (all use the same model)
agent_researcher_template = """
Human: You are Agent 1 - Researcher. Carefully analyze the context and the question.
Return a structured list of the most relevant facts, definitions, data, and citations
that should be considered. Do not write a narrative answer.
<context>
{context}
</context>

Question: {question}

Respond with clear bullet points only.

Assistant:"""

AGENT_RESEARCHER_PROMPT = PromptTemplate(
    template=agent_researcher_template, input_variables=["context", "question"]
)

agent_writer_template = """
Human: You are Agent 2 - Writer. Using the context and the Researcher notes below,
compose a comprehensive, well-structured draft answer of at least 250 words.
Ensure clarity and actionable guidance.
<context>
{context}
</context>

Question: {question}

Researcher notes:
{notes}

Assistant:"""

AGENT_WRITER_PROMPT = PromptTemplate(
    template=agent_writer_template, input_variables=["context", "question", "notes"]
)

agent_critic_template = """
Human: You are Agent 3 - Reviewer. Improve the draft for correctness, completeness,
clarity, and tone. Fix any issues and ensure it directly answers the question.
Cite relevant facts concisely.
<context>
{context}
</context>

Question: {question}

Draft to review:
{draft}

Assistant:"""

AGENT_CRITIC_PROMPT = PromptTemplate(
    template=agent_critic_template, input_variables=["context", "question", "draft"]
)

def _qa_with_prompt(llm, vectorstore_faiss, query, prompt):
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore_faiss.as_retriever(search_type="similarity", search_kwargs={"k": 3}),
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt},
    )
    answer = qa({"query": query})
    return answer["result"]


def get_response_llm(llm, vectorstore_faiss, query):
    return _qa_with_prompt(llm, vectorstore_faiss, query, PROMPT)


def run_three_agent_sonnet(llm, vectorstore_faiss, user_question):
    # Agent 1: Researcher
    researcher_notes = _qa_with_prompt(llm, vectorstore_faiss, user_question, AGENT_RESEARCHER_PROMPT)

    # Agent 2: Writer (uses Researcher notes)
    # We inject notes into the "question" field for the template using a small wrapper prompt
    # by formatting a composite question that the PromptTemplate expects.
    writer_prompt = PromptTemplate(
        template=AGENT_WRITER_PROMPT.template,
        input_variables=["context", "question"],
        partial_variables={"notes": researcher_notes},
    )
    writer_draft = _qa_with_prompt(llm, vectorstore_faiss, user_question, writer_prompt)

    # Agent 3: Reviewer (uses Writer draft)
    critic_prompt = PromptTemplate(
        template=AGENT_CRITIC_PROMPT.template,
        input_variables=["context", "question"],
        partial_variables={"draft": writer_draft},
    )
    final_answer = _qa_with_prompt(llm, vectorstore_faiss, user_question, critic_prompt)

    return final_answer, researcher_notes, writer_draft


def main():
    st.set_page_config("Chat PDF")

    st.header("Chat with PDF using AWS Bedrock💁")

    user_question = st.text_input("Ask a Question from the PDF Files")

    with st.sidebar:
        st.title("Update Or Create Vector Store:")

        if st.button("Vectors Update"):
            with st.spinner("Processing..."):
                docs = data_ingestion()
                get_vector_store(docs)
                st.success("Done")

    if st.button("Claude Sonnet Output"):
        with st.spinner("Processing..."):
            faiss_index = FAISS.load_local("faiss_index", bedrock_embeddings)
            llm = get_claude_llm()
            st.write(get_response_llm(llm, faiss_index, user_question))
            st.success("Done")

    if st.button("Run 3-Agent Sonnet"):
        with st.spinner("Processing with 3 agents..."):
            faiss_index = FAISS.load_local("faiss_index", bedrock_embeddings)
            llm = get_claude_llm()
            final_answer, researcher_notes, writer_draft = run_three_agent_sonnet(
                llm, faiss_index, user_question
            )
            st.subheader("Final Answer")
            st.write(final_answer)
            with st.expander("Agent 1 - Researcher notes"):
                st.write(researcher_notes)
            with st.expander("Agent 2 - Writer draft"):
                st.write(writer_draft)
            st.success("Done")

    if st.button("Llama2 Output"):
        with st.spinner("Processing..."):
            faiss_index = FAISS.load_local("faiss_index", bedrock_embeddings)
            llm = get_llama2_llm()
            st.write(get_response_llm(llm, faiss_index, user_question))
            st.success("Done")

if __name__ == "__main__":
    main()
