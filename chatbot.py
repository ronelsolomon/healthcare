import streamlit as st
from ctransformers import AutoModelForCausalLM
from pathlib import Path
import sqlite3
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain.chains import create_sql_query_chain

# Set page config
st.set_page_config(page_title="Healthcare Data Chatbot", page_icon="💬")

# Title and description
st.title("Healthcare Marketplace Chatbot (Local LLM)")
st.write("Ask questions about healthcare plans, benefits, and costs.")

# Initialize LLM model
@st.cache_resource
def load_llm():
    try:
        # Using a smaller model that works well locally
        model = AutoModelForCausalLM.from_pretrained(
            "TheBloke/Llama-2-7B-Chat-GGUF",
            model_file="llama-2-7b-chat.Q4_K_M.gguf",
            model_type="llama",
            context_length=2048
        )
        return model
    except Exception as e:
        st.error(f"Error loading model: {str(e)}")
        st.stop()

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask a question about the healthcare plans..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Process the query
    with st.chat_message("assistant"):
        with st.spinner("Analyzing data..."):
            try:
                # Simple LLM response without SQL for now
                llm = load_llm()
                response = llm(f"Answer the following question about healthcare plans: {prompt}")
                
                # Display the response
                st.markdown(response)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Add a sidebar with example questions
with st.sidebar:
    st.subheader("Example Questions")
    examples = [
        "What types of healthcare plans are available?",
        "What are the benefits of gold plans?",
        "How do deductibles work?",
        "What's the difference between HMO and PPO plans?",
        "How do I choose the right healthcare plan?"
    ]
    
    for example in examples:
        if st.button(example, key=example):
            st.session_state.messages.append({"role": "user", "content": example})
            st.rerun()
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("This chatbot uses a local language model to answer questions about healthcare plans.")