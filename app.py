"""
Streamlit UI for ADB Course RAG System
Simple, professional chat interface with sources display and feedback.
"""

import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.self_learning import SelfLearningRAG
from src.config import config


# Page configuration
st.set_page_config(
    page_title="ADB Course RAG System",
    page_icon="📚",
    layout="wide"
)
# Custom CSS - Professional Dark Mode
st.markdown("""
<style>
    /* Main app background */
    .stApp {
        background-color: #0F172A;
    }
    
    /* Headers */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #F8FAFC;
        margin-bottom: 0;
        text-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
    }
    
    .sub-header {
        font-size: 1rem;
        color: #94A3B8;
        margin-top: 0;
    }
    
    /* Source cards - dark theme */
    .source-card {
        background: linear-gradient(145deg, #1E293B, #0F172A);
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 15px;
        border-left: 4px solid #3B82F6;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease;
    }
    
    .source-card:hover {
        transform: translateX(5px);
        box-shadow: 0 6px 12px rgba(59, 130, 246, 0.2);
    }
    
    /* Response box - dark theme */
    .response-box {
        background: linear-gradient(145deg, #1E293B, #0F172A);
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #334155;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    }
    
    /* Text colors for dark mode */
    .stMarkdown, p, span, div {
        color: #E2E8F0;
    }
    
    /* Input fields */
    .stTextInput input, .stTextArea textarea {
        background-color: #1E293B;
        color: #F8FAFC;
        border: 1px solid #334155;
        border-radius: 8px;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #3B82F6;
        box-shadow: 0 0 0 1px #3B82F6;
    }
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(135deg, #3B82F6, #2563EB);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        background: linear-gradient(135deg, #2563EB, #1D4ED8);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
        transform: translateY(-2px);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0F172A;
        border-right: 1px solid #1E293B;
    }
    
    /* Metrics and cards */
    [data-testid="stMetric"] {
        background-color: #1E293B;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #334155;
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #0F172A;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #334155;
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #475569;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_rag_system():
    """Initialize and cache RAG system."""
    rag = SelfLearningRAG()
    if not rag.is_ready:
        with st.spinner("Building index from PDFs..."):
            rag.initialize()
    return rag


def main():
    # Header
    st.markdown('<p class="main-header">📚 ADB Course RAG Assistant</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Ask questions about the Advanced Databases course materials</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Initialize session state
    if 'selected_example' not in st.session_state:
        st.session_state['selected_example'] = ""
    
    # Initialize RAG system
    try:
        rag = get_rag_system()
    except Exception as e:
        st.error(f"Failed to initialize RAG system: {e}")
        st.stop()
    
    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Settings")
        
        top_k = st.slider(
            "Number of Sources (Top-K)",
            min_value=1,
            max_value=10,
            value=5
        )
        
        enable_expansion = st.checkbox(
            "Enable Query Expansion",
            value=True,
            help="Automatically improve unclear queries"
        )
        
        st.markdown("---")
        
        # System stats
        st.header("📊 System Info")
        stats = rag.pipeline.retriever.get_statistics()
        st.metric("Documents Indexed", stats.get('num_documents', 0))
        st.metric("Semantic Weight", f"{stats.get('semantic_weight', 0.7):.0%}")
        st.metric("Keyword Weight", f"{stats.get('keyword_weight', 0.3):.0%}")
        
        st.markdown("---")
        
        # Feedback stats
        learning_stats = rag.get_learning_stats()
        st.header("🧠 Learning Stats")
        total_fb = learning_stats['feedback'].get('total', 0)
        positive = learning_stats['feedback'].get('positive', 0)
        st.metric("Total Feedback", total_fb)
        if total_fb > 0:
            st.metric("Satisfaction Rate", f"{positive/total_fb:.0%}")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Use selected example as default if available
        default_val = st.session_state.get('selected_example', "")
        
        # Query input
        query = st.text_input(
            "Your Question",
            value=default_val,
            placeholder="Ask about databases, SQL, indexing, transactions..."
        )
        
        # Clear the selected example after using it
        if default_val:
            st.session_state['selected_example'] = ""
        
        # Query button
        if st.button("🔍 Ask", type="primary", use_container_width=True):
            if query.strip():
                with st.spinner("Searching and generating response..."):
                    try:
                        result, metadata = rag.query(
                            question=query,
                            enable_expansion=enable_expansion,
                            top_k=top_k
                        )
                        
                        # Store in session state
                        st.session_state['last_result'] = result
                        st.session_state['last_metadata'] = metadata
                        
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        # Display response
        if 'last_result' in st.session_state:
            result = st.session_state['last_result']
            metadata = st.session_state['last_metadata']
            
            # Show expansion info
            if metadata.get('was_expanded'):
                st.info(f"🔄 Query expanded to: \"{metadata['expanded_query']}\"")
            
            # Response
            st.markdown("### 📝 Answer")
            st.markdown(f'<div class="response-box">{result.response}</div>', unsafe_allow_html=True)
            
            # Feedback buttons
            st.markdown("#### Rate this response")
            fb1, fb2, _ = st.columns([1, 1, 3])
            
            with fb1:
                if st.button("👍 Helpful"):
                    rag.submit_feedback("positive")
                    st.success("Thanks!")
            
            with fb2:
                if st.button("👎 Not Helpful"):
                    rag.submit_feedback("negative")
                    st.warning("Thanks for feedback!")
    
    with col2:
        st.markdown("### 📄 Retrieved Sources")
        
        if 'last_result' in st.session_state:
            result = st.session_state['last_result']
            
            if result.sources:
                for source in result.sources:
                    st.markdown(f"""
                    <div class="source-card">
                        <strong>[{source['rank']}] {source['source']}</strong> (Page {source['page']})<br>
                        <small>Score: {source['score']:.3f}</small><br>
                        <em>{source['preview'][:100]}...</em>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No sources retrieved")
        else:
            st.info("Sources will appear here after asking a question")
    
    # Example questions (as text suggestions)
    st.markdown("---")
    st.markdown("### 💡 Try asking:")
    st.markdown("""
    - What are the ACID properties?
    - Explain B+ tree indexing
    - SQL vs NoSQL difference
    - How do transactions work?
    - What is database normalization?
    """)
    
    # Footer
    st.markdown("---")
    st.markdown("*Made with ❤️ for ADB Course | Hybrid RAG with FAISS + BM25 | Self-Learning Enabled*")


if __name__ == "__main__":
    main()
