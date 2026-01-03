"""
Chat History Persistence Module
Handles saving and loading chat history to/from JSON files or AWS S3.
Supports multiple chat sessions with unique IDs.
Automatically uses S3 if configured, falls back to local storage.
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False

# Storage Configuration
S3_BUCKET_NAME = os.getenv("CHAT_HISTORY_S3_BUCKET", "")
S3_PREFIX = "chat_history/"  # Prefix for all chat history files in S3
USE_S3 = S3_AVAILABLE and S3_BUCKET_NAME

# Local fallback directory
CHAT_HISTORY_DIR = Path("chat_history")
SESSIONS_INDEX_FILE = "sessions_index.json"

def ensure_history_dir():
    """Ensure the local chat history directory exists (for fallback)."""
    if not USE_S3:
        CHAT_HISTORY_DIR.mkdir(exist_ok=True)

def get_s3_client():
    """Get S3 client if credentials are available."""
    if not S3_AVAILABLE or not USE_S3:
        return None
    try:
        return boto3.client(
            's3',
            region_name=os.getenv("AWS_REGION", "us-east-2"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=os.getenv("AWS_SESSION_TOKEN")
        )
    except:
        return None

def get_s3_key(filename: str) -> str:
    """Get S3 key for a file."""
    return f"{S3_PREFIX}{filename}"

def s3_get_json(s3_client, key: str) -> Optional[Dict]:
    """Read JSON from S3."""
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=key)
        content = response['Body'].read().decode('utf-8')
        return json.loads(content)
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            return None
        print(f"S3 error reading {key}: {str(e)}")
        return None
    except Exception as e:
        print(f"Error reading from S3: {str(e)}")
        return None

def s3_put_json(s3_client, key: str, data: Dict):
    """Write JSON to S3."""
    try:
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=key,
            Body=json.dumps(data, indent=2, ensure_ascii=False),
            ContentType='application/json'
        )
        return True
    except Exception as e:
        print(f"Error writing to S3: {str(e)}")
        return False

def get_sessions_index() -> Dict:
    """Load the sessions index file from S3 or local."""
    if USE_S3:
        s3_client = get_s3_client()
        if s3_client:
            index = s3_get_json(s3_client, get_s3_key(SESSIONS_INDEX_FILE))
            if index is not None:
                return index
    
    # Fallback to local
    ensure_history_dir()
    local_file = CHAT_HISTORY_DIR / SESSIONS_INDEX_FILE
    if not local_file.exists():
        return {}
    try:
        with open(local_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading local sessions index: {str(e)}")
        return {}

def save_sessions_index(index: Dict):
    """Save the sessions index file to S3 or local."""
    if USE_S3:
        s3_client = get_s3_client()
        if s3_client:
            if s3_put_json(s3_client, get_s3_key(SESSIONS_INDEX_FILE), index):
                return True
    
    # Fallback to local
    ensure_history_dir()
    try:
        local_file = CHAT_HISTORY_DIR / SESSIONS_INDEX_FILE
        with open(local_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving local sessions index: {str(e)}")
        return False

def get_session_file(session_id: str) -> str:
    """Get the filename for a specific session."""
    return f"session_{session_id}.json"

def create_new_session(title: str = None) -> str:
    """
    Create a new chat session.
    
    Args:
        title: Optional title for the session (will use first message if not provided)
    
    Returns:
        Session ID (UUID string)
    """
    session_id = str(uuid.uuid4())
    index = get_sessions_index()
    
    # Generate title from first message or use default
    if not title:
        title = f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    index[session_id] = {
        "title": title,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "message_count": 0
    }
    
    save_sessions_index(index)
    return session_id

def save_chat_history(session_id: str, messages: list, memory_messages: list = None):
    """
    Save chat history for a specific session.
    
    Args:
        session_id: Unique session ID
        messages: List of message dicts with 'role' and 'content' keys
        memory_messages: Optional list of memory messages from ConversationBufferMemory
    """
    try:
        ensure_history_dir()
        
        # Generate title from first user message if not set
        index = get_sessions_index()
        if session_id not in index:
            # Create session entry if it doesn't exist
            first_user_msg = next((msg.get("content", "")[:50] for msg in messages if msg.get("role") == "user"), None)
            title = first_user_msg if first_user_msg else f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            index[session_id] = {
                "title": title,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "message_count": len(messages)
            }
        else:
            # Update existing session
            if not index[session_id].get("title") or index[session_id]["title"].startswith("Chat "):
                # Update title from first message if it's still default
                first_user_msg = next((msg.get("content", "")[:50] for msg in messages if msg.get("role") == "user"), None)
                if first_user_msg:
                    index[session_id]["title"] = first_user_msg
            
            index[session_id]["updated_at"] = datetime.now().isoformat()
            index[session_id]["message_count"] = len(messages)
        
        # Prepare history data
        history_data = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "messages": messages,
            "total_messages": len(messages)
        }
        
        # If memory messages are provided, also save them in a format we can restore
        if memory_messages:
            memory_data = []
            for msg in memory_messages:
                msg_type = getattr(msg, "type", None)
                content = getattr(msg, "content", str(msg))
                memory_data.append({
                    "type": msg_type,
                    "content": content
                })
            history_data["memory_messages"] = memory_data
        
        # Save session file to S3 or local
        filename = get_session_file(session_id)
        
        if USE_S3:
            s3_client = get_s3_client()
            if s3_client:
                if s3_put_json(s3_client, get_s3_key(filename), history_data):
                    save_sessions_index(index)
                    return True
        
        # Fallback to local
        ensure_history_dir()
        session_file = CHAT_HISTORY_DIR / filename
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, indent=2, ensure_ascii=False)
        
        # Update index
        save_sessions_index(index)
        
        return True
    except Exception as e:
        print(f"Error saving chat history: {str(e)}")
        return False

def load_chat_history(session_id: str) -> Tuple[Optional[List], Optional[List]]:
    """
    Load chat history for a specific session from S3 or local.
    
    Args:
        session_id: Unique session ID
    
    Returns:
        Tuple of (messages list, memory_messages list) or (None, None) if not found
    """
    try:
        filename = get_session_file(session_id)
        
        # Try S3 first
        if USE_S3:
            s3_client = get_s3_client()
            if s3_client:
                history_data = s3_get_json(s3_client, get_s3_key(filename))
                if history_data:
                    messages = history_data.get("messages", [])
                    memory_messages = history_data.get("memory_messages", [])
                    return messages, memory_messages
        
        # Fallback to local
        session_file = CHAT_HISTORY_DIR / filename
        if not session_file.exists():
            return None, None
        
        with open(session_file, 'r', encoding='utf-8') as f:
            history_data = json.load(f)
        
        messages = history_data.get("messages", [])
        memory_messages = history_data.get("memory_messages", [])
        
        return messages, memory_messages
    except Exception as e:
        print(f"Error loading chat history: {str(e)}")
        return None, None

def get_all_sessions() -> List[Dict]:
    """
    Get all chat sessions sorted by most recent.
    
    Returns:
        List of session dicts with id, title, updated_at, message_count
    """
    index = get_sessions_index()
    sessions = []
    
    for session_id, session_data in index.items():
        sessions.append({
            "id": session_id,
            "title": session_data.get("title", "Untitled Chat"),
            "updated_at": session_data.get("updated_at", ""),
            "message_count": session_data.get("message_count", 0),
            "created_at": session_data.get("created_at", "")
        })
    
    # Sort by updated_at (most recent first)
    sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return sessions

def update_session_title(session_id: str, new_title: str) -> bool:
    """
    Update the title of a chat session.
    
    Args:
        session_id: Unique session ID
        new_title: New title for the session
    
    Returns:
        True if successful, False otherwise
    """
    try:
        index = get_sessions_index()
        if session_id in index:
            index[session_id]["title"] = new_title
            index[session_id]["updated_at"] = datetime.now().isoformat()
            save_sessions_index(index)
            return True
        return False
    except Exception as e:
        print(f"Error updating session title: {str(e)}")
        return False

def delete_session(session_id: str) -> bool:
    """
    Delete a chat session.
    
    Args:
        session_id: Unique session ID
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Remove from index
        index = get_sessions_index()
        if session_id in index:
            del index[session_id]
            save_sessions_index(index)
        
        # Delete session file from S3 or local
        filename = get_session_file(session_id)
        
        if USE_S3:
            s3_client = get_s3_client()
            if s3_client:
                try:
                    s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=get_s3_key(filename))
                except Exception as e:
                    print(f"Error deleting from S3: {str(e)}")
        
        # Also delete locally if exists (for cleanup)
        session_file = CHAT_HISTORY_DIR / filename
        if session_file.exists():
            session_file.unlink()
        
        return True
    except Exception as e:
        print(f"Error deleting session: {str(e)}")
        return False


def restore_memory_from_history(memory_messages: list, create_memory_func):
    """
    Restore ConversationBufferMemory from saved history.
    
    Args:
        memory_messages: List of saved memory message dicts
        create_memory_func: Function to create a new memory instance
    
    Returns:
        Restored ConversationBufferMemory instance
    """
    memory = create_memory_func()
    
    if not memory_messages:
        return memory
    
    # Restore messages to memory in pairs (human input, ai output)
    current_input = None
    for msg_data in memory_messages:
        msg_type = msg_data.get("type")
        content = msg_data.get("content", "")
        
        if msg_type == "human":
            # If we have a previous input without an output, save it with empty output
            if current_input is not None:
                memory.save_context({"input": current_input}, {"output": ""})
            current_input = content
        elif msg_type == "ai" and current_input is not None:
            # Save the pair: human input + AI output
            memory.save_context({"input": current_input}, {"output": content})
            current_input = None
    
    # Handle case where last message is human without AI response
    if current_input is not None:
        memory.save_context({"input": current_input}, {"output": ""})
    
    return memory

def get_session_info(session_id: str) -> Optional[Dict]:
    """
    Get information about a specific session.
    
    Args:
        session_id: Unique session ID
    
    Returns:
        Dict with session info or None if not found
    """
    index = get_sessions_index()
    if session_id not in index:
        return None
    
    session_data = index[session_id].copy()
    session_data["id"] = session_id
    return session_data

