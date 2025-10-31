"""
Career Path Recommender System - Simple Chat Interface
"""

import asyncio
import streamlit as st
from agents.simple_career_agent import analyze_career_goal, get_bedrock_client, create_memory

# Page config
st.set_page_config(page_title="Your Personal AI Agent", page_icon="🤖")

# Initialize session state - each user gets their own isolated memory
if "messages" not in st.session_state:
    st.session_state.messages = []
if "bedrock_client" not in st.session_state:
    st.session_state.bedrock_client = get_bedrock_client()
if "memory" not in st.session_state:
    st.session_state.memory = create_memory()  # Each session gets its own memory instance

# Header
st.title("Your Personal AI Agent")
st.caption("Mentor, friend, and expert—here to help you with life, work, interviews, learning, or any problem.")

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
                response = analyze_career_goal(
                    st.session_state.bedrock_client,
                    prompt,
                    memory=st.session_state.memory  # Pass session-specific memory
                )
                st.write(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Clear chat button
if st.button("Clear Chat"):
    st.session_state.messages = []
    st.session_state.memory = create_memory()  # Reset memory for new conversation
    st.rerun()
