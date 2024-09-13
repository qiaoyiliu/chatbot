import streamlit as st
import requests
from bs4 import BeautifulSoup
from openai import OpenAI

# Show title and description
st.title("💬 Chatbot with URL Summarization")
st.write(
    "This is a chatbot that uses OpenAI's GPT-4o-mini model to generate responses and summarize URLs. "
    "To use this app, provide an OpenAI API key, and optionally upload a URL for summarization."
)

# Ask user for OpenAI API key via st.text_input.
openai_api_key = st.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.info("Please add your OpenAI API key to continue.", icon="🗝️")
else:
    # Sidebar for memory management options.
    memory_option = st.sidebar.radio(
        "Choose how to store memory:",
        ("Last 5 questions", "Summary of entire conversation", "Last 5,000 tokens")
    )

    # URL input field
    url_input = st.text_input("Enter a URL to summarize:")
    
    # Initialize OpenAI client
    client = OpenAI(api_key=openai_api_key)

    # Initialize session state for messages and URL summary
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "url_summary" not in st.session_state:
        st.session_state.url_summary = ""

    # If a URL is uploaded
    if url_input:
        try:
            # Retrieve the content of the URL
            response = requests.get(url_input)
            soup = BeautifulSoup(response.content, "html.parser")
            url_text = soup.get_text()

            # Summarize the content using the OpenAI API
            summary_prompt = f"Summarize the following content: {url_text[:2000]}"  # Limit content to avoid exceeding token limits
            summary_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": summary_prompt}]
            )
            url_summary = summary_response['choices'][0]['message']['content']

            # Store the URL summary in session state
            st.session_state.url_summary = url_summary

            # Display the summary
            st.success("URL successfully summarized:")
            st.write(url_summary)

        except Exception as e:
            st.error(f"Failed to retrieve or process the URL. Error: {e}")

    # Display the existing chat messages.
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input field for user messages
    if prompt := st.chat_input("What is up?"):

        # Store and display the current prompt
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Adjust memory based on the user's selection
        if memory_option == "Last 5 questions":
            # Keep only the last 5 user and assistant messages
            st.session_state.messages = st.session_state.messages[-10:]
        elif memory_option == "Summary of entire conversation":
            # Summarize the conversation and keep only the summary
            conversation_summary = "\n".join(
                [f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages]
            )
            st.session_state.messages = [{"role": "system", "content": conversation_summary}]
        elif memory_option == "Last 5,000 tokens":
            # Ensure the conversation doesn't exceed 5,000 tokens (simplified)
            conversation_text = "\n".join([msg["content"] for msg in st.session_state.messages])
            if len(conversation_text) > 5000:
                st.session_state.messages = st.session_state.messages[-100:]

        # Generate a response using OpenAI API, combining URL summary and chat history
        messages_with_summary = [{"role": "system", "content": st.session_state.url_summary}] + \
                                [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages_with_summary
        )

        # Stream the response to the chat
        assistant_message = response['choices'][0]['message']['content']
        with st.chat_message("assistant"):
            st.markdown(assistant_message)
        st.session_state.messages.append({"role": "assistant", "content": assistant_message})
