import streamlit as st
import requests
from bs4 import BeautifulSoup
import openai

# Function to fetch URL content
def fetch_url_content(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup.get_text()
    except Exception as e:
        return f"Error fetching content from URL: {e}"

# Function to summarize the URL content using the new OpenAI API (v1.0.0 and above)
def summarize_content(content, api_key):
    openai.api_key = api_key
    response = openai.completions.create(
        model="gpt-4",  # Use the appropriate model
        prompt=f"Summarize the following content: {content}",
        max_tokens=150,
    )
    return response.choices[0].text.strip()

# Function to chat with memory (summary + chat history) using the new OpenAI API (v1.0.0 and above)
def chat_with_memory(user_input, api_key):
    prompt = "\n".join([msg['content'] for msg in st.session_state['messages']]) + \
             "\nSummary: " + "\n".join(st.session_state['url_summaries']) + \
             "\nUser: " + user_input
             
    openai.api_key = api_key
    response = openai.completions.create(
        model="gpt-4",  # Use the appropriate model
        prompt=prompt,
        max_tokens=200,
    )
    return response.choices[0].text.strip()

# Streamlit chatbot app
st.title("💬 Chatbot with URL Summarization")
st.write(
    "This chatbot summarizes URLs and chats with memory. Provide an API key and a URL to start."
)

# Ask for OpenAI API key
openai_api_key = st.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.info("Please provide your OpenAI API key to continue.", icon="🗝️")
else:
    # Sidebar for memory management
    memory_option = st.sidebar.radio(
        "Memory management method:",
        ("Last 5 questions", "Summary of entire conversation", "Last 5,000 tokens")
    )

    # URL input field
    url_input = st.text_input("Enter a URL to summarize:")

    # Initialize session state for messages and summaries
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "url_summaries" not in st.session_state:
        st.session_state['url_summaries'] = []

    # If a URL is provided
    if url_input:
        with st.spinner("Fetching and summarizing URL content..."):
            url_content = fetch_url_content(url_input)
            if "Error" in url_content:
                st.error(url_content)  # Display error if content cannot be fetched
            else:
                summary = summarize_content(url_content[:2000], openai_api_key)  # Limit content to avoid token limits
                st.session_state['url_summaries'].append(summary)
                st.success("URL summarized successfully!")
                st.write(summary)

    # Display existing messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input field for user messages
    if prompt := st.chat_input("What's on your mind?"):

        # Store and display the user's message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Adjust memory based on user's selection
        if memory_option == "Last 5 questions":
            st.session_state.messages = st.session_state.messages[-10:]
        elif memory_option == "Summary of entire conversation":
            conversation_summary = "\n".join(
                [f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages]
            )
            st.session_state.messages = [{"role": "system", "content": conversation_summary}]
        elif memory_option == "Last 5,000 tokens":
            conversation_text = "\n".join([msg["content"] for msg in st.session_state.messages])
            if len(conversation_text) > 5000:
                st.session_state.messages = st.session_state.messages[-100:]

        # Generate response using chat_with_memory
        assistant_message = chat_with_memory(prompt, openai_api_key)

        # Display assistant's message and append it to session state
        with st.chat_message("assistant"):
            st.markdown(assistant_message)
        st.session_state.messages.append({"role": "assistant", "content": assistant_message})
