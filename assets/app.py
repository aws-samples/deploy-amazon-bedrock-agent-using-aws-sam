# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import streamlit as st
import boto3
import json
import datetime
import logging
import uuid
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the Bedrock Agent Runtime client
bedrock_agent_runtime_client = boto3.client(
    "bedrock-agent-runtime", region_name="us-west-2"
)

# # Initialize the Bedrock Agent Runtime client
# bedrock_agent_runtime_client = boto3.client(
#     "bedrock-agent-runtime", region_name="us-east-1"
# )

# Dictionary mapping names to their data
citizen_data = {
    "Tom": {"district_id": 4, "citizen_id": 2, "name": "Tom"},
    "Heather": {"district_id": 1, "citizen_id": 8, "name": "Heather"},
    "Frank": {"district_id": 3, "citizen_id": 3, "name": "Frank"},
}

# Page configuration
st.set_page_config(
    page_title="AnyCity USA Assistant",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS styling with city theme
st.markdown(
    """
    <style>
    .main {
        padding: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: flex-start;
    }
    .user-message {
        background-color: #e6f3ff;
        border-left: 4px solid #1e88e5;
    }
    .assistant-message {
        background-color: #f0f0f0;
        border-left: 4px solid #4caf50;
    }
    .trace-message {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        font-family: monospace;
        font-size: 0.9em;
    }
    .sidebar-content {
        padding: 1rem;
    }
    .stButton button {
        width: 100%;
        margin-top: 1rem;
    }
    .city-header {
        color: #1e88e5;
        text-align: center;
        margin-bottom: 2rem;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "show_traces" not in st.session_state:
    st.session_state.show_traces = False
if "trace_data" not in st.session_state:
    st.session_state.trace_data = []

# Sidebar configuration
with st.sidebar:
    st.title("🏙️ AnyCity USA")
    st.markdown("---")

    # Agent Configuration Section
    st.subheader("🤖 Agent Configuration")
    agent_id = st.text_input(
        "Agent ID",
        value=st.session_state.get("agent_id", ""),
        help="Enter your AnyCity USA Agent ID",
    )

    agent_alias_id = st.text_input(
        "Agent Alias ID",
        value=st.session_state.get("agent_alias_id", ""),
        help="Enter your AnyCity USA Agent Alias ID",
    )

    # Sidebar dropdown
    selected_citizen = st.sidebar.selectbox(
        "Select Citizen", options=list(citizen_data.keys())
    )

    # # Display selected citizen's data
    # if selected_citizen:
    #     st.write(f"District ID: {citizen_data[selected_citizen]['district_id']}")
    #     st.write(f"Citizen ID: {citizen_data[selected_citizen]['citizen_id']}")
    #     st.write(f"Name: {citizen_data[selected_citizen]['name']}")

    # Session Management Section
    st.markdown("---")
    st.subheader("📝 Session Management")

    if st.button("🔄 Generate New Session"):
        st.session_state.session_id = str(uuid.uuid4())
        st.success(f"New session started!")

    st.text_input(
        "Current Session ID", value=st.session_state.session_id, disabled=True
    )

    # Debug Options Section
    st.markdown("---")
    st.subheader("🔧 Debug Options")

    # Trace Toggle
    show_traces = st.toggle("Show Agent Traces", value=st.session_state.show_traces)
    if show_traces != st.session_state.show_traces:
        st.session_state.show_traces = show_traces
        st.rerun()

    # Clear Chat with Session End
    st.markdown("---")
    if st.button("🗑️ Clear Chat & End Session"):
        try:
            if st.session_state.messages:
                simple_agent_invoke(
                    input_text="end session",
                    agent_id=agent_id,
                    agent_alias_id=agent_alias_id,
                    session_id=st.session_state.session_id,
                    end_session=True,
                )
        except Exception as e:
            logger.error(f"Error ending session: {e}")

        # Clear all session data
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.trace_data = []
        st.success("Chat cleared and new session started!")


# Agent interaction function
def simple_agent_invoke(
    input_text, agent_id, agent_alias_id, session_id=None, end_session=False
):
    """
    Invoke the Bedrock agent and handle the response stream
    """
    try:
        agent_response = bedrock_agent_runtime_client.invoke_agent(
            inputText=input_text,
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            enableTrace=True,  # Always enable trace collection
            endSession=end_session,
        )

        event_stream = agent_response["completion"]
        response_content = []
        trace_content = []

        for event in event_stream:
            if "chunk" in event:
                data = event["chunk"]["bytes"]
                chunk_text = data.decode("utf-8")
                response_content.append(chunk_text)
                logger.info(f"Chunk received: {chunk_text}")

            elif "trace" in event:
                trace_data = event["trace"]
                trace_content.append(trace_data)
                logger.info(f"Trace data received: {json.dumps(trace_data, indent=2)}")

        return "".join(response_content), trace_content

    except Exception as e:
        logger.error(f"Error in agent invocation: {e}")
        raise e


# Display chat messages
def display_message(message):
    role = message["role"]
    content = message["content"]
    timestamp = message.get(
        "timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    with st.chat_message(role):
        st.markdown(f"*{timestamp}*")
        st.markdown(content)

        # Display traces if they exist and traces are enabled
        if (
            role == "assistant"
            and st.session_state.show_traces
            and "trace_data" in message
        ):
            with st.expander("View Agent Traces"):
                for trace in message["trace_data"]:
                    st.code(json.dumps(trace, indent=2))


# Main chat interface
st.title("🏙️ AnyCity USA Assistant")
st.markdown(
    """
    <div class="city-header">
        Your AI-powered guide to city services, information, and assistance
    </div>
""",
    unsafe_allow_html=True,
)

# Input validation
if not agent_id or not agent_alias_id:
    st.warning(
        "Please configure the Agent ID and Agent Alias ID in the sidebar to begin."
    )
    st.stop()

# Display chat history
for message in st.session_state.messages:
    display_message(message)

# Chat input
if user_input := st.chat_input("How can I help you with AnyCity services today?"):
    # Add user message to chat
    user_message = {
        "role": "user",
        "content": user_input,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    st.session_state.messages.append(user_message)
    display_message(user_message)

    try:
        # Get agent response with traces
        response_text, trace_data = simple_agent_invoke(
            input_text=user_input,
            agent_id=agent_id,
            agent_alias_id=agent_alias_id,
            session_id=st.session_state.session_id,
        )

        # Add assistant message to chat with trace data
        assistant_message = {
            "role": "assistant",
            "content": response_text,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "trace_data": trace_data if trace_data else [],
        }
        st.session_state.messages.append(assistant_message)
        display_message(assistant_message)

    except Exception as e:
        st.error(f"Error: {str(e)}")
        logger.error(f"Error processing message: {e}")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <small>
            AnyCity USA Assistant | Powered by Amazon Bedrock | Version 2.0
        </small>
    </div>
    """,
    unsafe_allow_html=True,
)
