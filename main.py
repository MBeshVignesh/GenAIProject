"""
Career Path Recommender System - Simple Chat Interface
"""

import asyncio
import streamlit as st
from agents.simple_career_agent import CareerAgent
from agents.course_catalog_agent import CourseCatalogAgent

# Page config
st.set_page_config(page_title="Career Assistant", page_icon="💼")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent" not in st.session_state:
    st.session_state.agent = None

# Header
st.title(" Your Career Assistant")
st.caption("Ask me about your career or courses!")

# Agent selection
agent_type = st.radio("Choose Agent:", ["Career Agent", "Course Agent"], horizontal=True)

# Initialize agent
if st.session_state.agent is None or st.session_state.get('current_agent') != agent_type:
    with st.spinner("Loading agent..."):
        if agent_type == "Career Agent":
            st.session_state.agent = CareerAgent()
        else:
            st.session_state.agent = CourseCatalogAgent()
        st.session_state.current_agent = agent_type

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
if prompt := st.chat_input("Ask me anything..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
    
    # Get response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = asyncio.run(st.session_state.agent.analyze(prompt))
                st.write(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Clear chat button
if st.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()
