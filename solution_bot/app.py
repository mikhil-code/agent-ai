import streamlit as st
from dotenv import load_dotenv
from utils1.doc_processor import process_document
from utils1.chat_manager import ChatManager
from utils1.vector_store import VectorStore
import os
import io

load_dotenv()


def handle_followup(question, chat_manager):
    response, new_follow_ups = chat_manager.get_response(question)
    return response, new_follow_ups

def main():
    st.title("Document Q&A Chatbot")
    
    # Initialize vector store
    vector_store = VectorStore()
    
    # Show database status
    if vector_store.vector_store is not None:
        st.info("📚 Previously loaded documents are available in the system")
    
    # File upload with explicit MIME types
    uploaded_file = st.file_uploader(
        "Upload additional document", 
        type=["docx", "pdf"],
        accept_multiple_files=False,
        help="Upload either a PDF or DOCX file"
    )

    if uploaded_file is not None:
        try:
            # Create BytesIO object for PDF files
            if uploaded_file.type == "application/pdf":
                file_bytes = io.BytesIO(uploaded_file.read())
                file_bytes.name = uploaded_file.name  # Add name attribute for process_document
            else:
                file_bytes = uploaded_file

            with st.spinner("Processing document..."):
                chunks = process_document(file_bytes)
                vector_store.add_texts(chunks)
            st.success(f"Document '{uploaded_file.name}' processed and saved successfully!")
        except Exception as e:
            st.error(f"Error processing document: {str(e)}")
            st.error("Please make sure the file is not corrupted and try again.")
    
    # Initialize session states
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_follow_ups" not in st.session_state:
        st.session_state.current_follow_ups = []
    if "message_counter" not in st.session_state:
        st.session_state.message_counter = 0
    
    chat_manager = ChatManager(vector_store)
    
    # Display chat messages
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
        # Show follow-up questions after assistant responses
        if message["role"] == "assistant" and "follow_ups" in message:
            st.markdown("**Follow-up questions:**")
            cols = st.columns(len(message["follow_ups"]))
            for i, question in enumerate(message["follow_ups"]):
                # Create unique key using message index and question index
                unique_key = f"follow_up_{st.session_state.message_counter}_{idx}_{i}"
                if cols[i].button(f"📝 {question}", key=unique_key):
                    response, follow_ups = chat_manager.get_response(question)
                    st.session_state.messages.extend([
                        {"role": "user", "content": question},
                        {"role": "assistant", "content": response, "follow_ups": follow_ups}
                    ])
                    st.session_state.message_counter += 1
                    st.experimental_rerun()
    
    # Clear chat button
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.session_state.message_counter = 0
        st.experimental_rerun()
    
    # User input and response
    if prompt := st.chat_input("Ask a question about your document"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        response, follow_ups = chat_manager.get_response(prompt)
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response,
            "follow_ups": follow_ups
        })
        st.session_state.message_counter += 1
        st.experimental_rerun()

if __name__ == "__main__":
    main()
