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
st.set_page_config(page_title="Your Personal AI Agent", page_icon="🤖", layout="wide")

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

# Sidebar with session management
with st.sidebar:
    st.header("💬 Chat Sessions")
    
    # New Chat button
    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        # Save current session before switching
        if st.session_state.messages:
            memory_vars = st.session_state.memory.load_memory_variables({})
            memory_messages = memory_vars.get("chat_history", [])
            save_chat_history(
                st.session_state.current_session_id,
                st.session_state.messages,
                list(memory_messages)
            )
        
        # Create new session
        st.session_state.current_session_id = create_new_session()
        st.session_state.messages = []
        st.session_state.memory = create_memory()
        st.session_state.session_switched = True
        st.rerun()
    
    st.divider()
    
    # List of previous sessions
    st.subheader("Previous Chats")
    sessions = get_all_sessions()
    
    if not sessions:
        st.info("No previous chats")
    else:
        # Filter out current session from list
        other_sessions = [s for s in sessions if s["id"] != st.session_state.current_session_id]
        
        if not other_sessions:
            st.info("No other chats")
        else:
            for session in other_sessions:
                col1, col2, col3 = st.columns([4, 1, 1])
                
                with col1:
                    # Format date
                    try:
                        from datetime import datetime
                        updated = datetime.fromisoformat(session["updated_at"])
                        date_str = updated.strftime("%b %d, %H:%M")
                    except:
                        date_str = "Recent"
                    
                    # Session button
                    session_label = f"💬 {session['title'][:40]}"
                    if len(session['title']) > 40:
                        session_label += "..."
                    session_label += f"\n_({session['message_count']} msgs, {date_str})_"
                    
                    if st.button(session_label, key=f"session_{session['id']}", use_container_width=True):
                        # Save current session before switching
                        if st.session_state.messages:
                            memory_vars = st.session_state.memory.load_memory_variables({})
                            memory_messages = memory_vars.get("chat_history", [])
                            save_chat_history(
                                st.session_state.current_session_id,
                                st.session_state.messages,
                                list(memory_messages)
                            )
                        
                        # Load selected session
                        st.session_state.current_session_id = session["id"]
                        saved_messages, saved_memory_messages = load_chat_history(session["id"])
                        
                        if saved_messages:
                            st.session_state.messages = saved_messages
                            if saved_memory_messages:
                                st.session_state.memory = restore_memory_from_history(saved_memory_messages, create_memory)
                            else:
                                st.session_state.memory = create_memory()
                        else:
                            st.session_state.messages = []
                            st.session_state.memory = create_memory()
                        
                        st.session_state.session_switched = True
                        st.rerun()
                
                with col2:
                    # Rename button
                    if st.button("✏️", key=f"rename_{session['id']}", help="Rename this chat"):
                        st.session_state[f"renaming_{session['id']}"] = True
                        st.rerun()
                
                with col3:
                    # Delete button
                    if st.button("🗑️", key=f"delete_{session['id']}", help="Delete this chat"):
                        delete_session(session["id"])
                        st.rerun()
                
                # Show rename input if this session is being renamed
                if st.session_state.get(f"renaming_{session['id']}", False):
                    new_title = st.text_input(
                        "New name:",
                        value=session['title'],
                        key=f"rename_input_{session['id']}",
                        label_visibility="collapsed"
                    )
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.button("Save", key=f"save_rename_{session['id']}", use_container_width=True):
                            if new_title and new_title.strip():
                                update_session_title(session["id"], new_title.strip())
                            st.session_state[f"renaming_{session['id']}"] = False
                            st.rerun()
                    with col_cancel:
                        if st.button("Cancel", key=f"cancel_rename_{session['id']}", use_container_width=True):
                            st.session_state[f"renaming_{session['id']}"] = False
                            st.rerun()

# Main content area
st.title("How can I help! ")
st.caption("Let's do some research and discuss strategy")

# Show current session info
current_session_info = None
try:
    sessions = get_all_sessions()
    current_session_info = next((s for s in sessions if s["id"] == st.session_state.current_session_id), None)
    if current_session_info:
        st.caption(f"📝 {current_session_info['title']}")
except:
    pass

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
                
                # Auto-save chat history after each exchange
                memory_vars = st.session_state.memory.load_memory_variables({})
                memory_messages = memory_vars.get("chat_history", [])
                save_chat_history(
                    st.session_state.current_session_id,
                    st.session_state.messages,
                    list(memory_messages)
                )
            except Exception as e:
                st.error(f"Error: {str(e)}")
