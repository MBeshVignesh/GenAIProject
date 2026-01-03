"""
Career Path Recommender System - Simple Chat Interface
"""

import asyncio
import streamlit as st
from agents.simple_career_agent import analyze_career_goal, get_bedrock_clients, create_memory
from chat_history import (
    save_chat_history, 
    load_chat_history, 
    create_new_session,
    get_all_sessions,
    delete_session,
    update_session_title,
    restore_memory_from_history
)

# Page config
st.set_page_config(page_title="Career Assistant", page_icon="💼")

# Initialize session state
if "current_session_id" not in st.session_state:
    # Get all sessions and load most recent, or create new one
    sessions = get_all_sessions()
    if sessions:
        # Load most recent session
        most_recent = sessions[0]  # Already sorted by most recent
        st.session_state.current_session_id = most_recent["id"]
        saved_messages, saved_memory_messages = load_chat_history(most_recent["id"])
        if saved_messages:
            st.session_state.messages = saved_messages
            if saved_memory_messages:
                st.session_state.memory = restore_memory_from_history(saved_memory_messages, create_memory)
            else:
                st.session_state.memory = create_memory()
        else:
            st.session_state.messages = []
            st.session_state.memory = create_memory()
    else:
        # Create a new session if none exists
        st.session_state.current_session_id = create_new_session()
        st.session_state.messages = []
        st.session_state.memory = create_memory()
    st.session_state.session_switched = False
else:
    st.session_state.session_switched = False

if "bedrock_runtime" not in st.session_state or "bedrock_agent_runtime" not in st.session_state:
    bedrock_runtime, bedrock_agent_runtime = get_bedrock_clients()
    st.session_state.bedrock_runtime = bedrock_runtime
    st.session_state.bedrock_agent_runtime = bedrock_agent_runtime

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
                response = analyze_career_goal(
                    st.session_state.bedrock_runtime,
                    st.session_state.bedrock_agent_runtime,
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
    st.rerun()
