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
import tempfile
import os


def process_uploaded_files(uploaded_files, rag):
    """Process uploaded PDF files with native Streamlit progress visualization."""
    from src.dynamic_updater import DynamicUpdatePipeline
    from pathlib import Path
    import time
    
    # Create styled header
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(59,130,246,0.1), rgba(139,92,246,0.1)); 
                padding: 20px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px;">
        <h3 style="margin: 0; color: #f8fafc;">📊 Processing Documents</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Stage indicators using columns
    stages = ['📤 Upload', '📄 Extract', '✂️ Chunk', '🧠 Embed', '💾 Index']
    stage_cols = st.columns(len(stages))
    stage_placeholders = []
    for i, (col, stage) in enumerate(zip(stage_cols, stages)):
        with col:
            stage_placeholders.append(st.empty())
    
    # Progress bar
    progress_bar = st.progress(0, text="Initializing...")
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        stage_metric = st.empty()
        stage_metric.metric("📊 Stage", "1/5")
    with col2:
        progress_metric = st.empty()
        progress_metric.metric("⚡ Progress", "0%")
    with col3:
        chunks_metric = st.empty()
        chunks_metric.metric("📦 Chunks", "0")
    with col4:
        time_metric = st.empty()
        time_metric.metric("⏱️ Time", "0.0s")
    
    # Status text
    status_placeholder = st.empty()
    
    # Details expander
    details = st.expander("📋 Processing Details", expanded=False)
    
    total_files = len(uploaded_files)
    total_chunks = 0
    total_actions = {'INSERT': 0, 'MERGE': 0, 'REPLACEMENT': 0}
    start_time = time.time()
    current_stage = 0
    
    def update_stages(active_stage):
        """Update stage indicators with visual feedback."""
        for i, placeholder in enumerate(stage_placeholders):
            if i < active_stage:
                placeholder.markdown(f"<div style='text-align:center;padding:8px;background:rgba(16,185,129,0.2);border-radius:8px;border:1px solid #10b981;'><span style='font-size:20px;'>✅</span><br><small style='color:#10b981;'>{stages[i].split()[1]}</small></div>", unsafe_allow_html=True)
            elif i == active_stage:
                placeholder.markdown(f"<div style='text-align:center;padding:8px;background:rgba(59,130,246,0.2);border-radius:8px;border:2px solid #3b82f6;animation:pulse 2s infinite;'><span style='font-size:20px;'>{stages[i].split()[0]}</span><br><small style='color:#3b82f6;font-weight:bold;'>{stages[i].split()[1]}</small></div>", unsafe_allow_html=True)
            else:
                placeholder.markdown(f"<div style='text-align:center;padding:8px;background:rgba(100,116,139,0.1);border-radius:8px;border:1px solid #334155;opacity:0.5;'><span style='font-size:20px;'>{stages[i].split()[0]}</span><br><small style='color:#64748b;'>{stages[i].split()[1]}</small></div>", unsafe_allow_html=True)
    
    try:
        # Initialize
        update_stages(0)
        status_placeholder.info("🔄 Initializing pipeline...")
        
        pipeline = DynamicUpdatePipeline(
            rag.pipeline.retriever.vector_store,
            rag.pipeline.generator.client
        )
        
        for file_idx, uploaded_file in enumerate(uploaded_files):
            # Stage 1: Upload
            current_stage = 0
            update_stages(current_stage)
            progress_bar.progress(0.02, text=f"📤 Uploading: {uploaded_file.name}")
            status_placeholder.info(f"📤 Uploading: {uploaded_file.name}")
            stage_metric.metric("📊 Stage", "1/5 Upload")
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = Path(tmp.name)
            
            try:
                def progress_callback(stage, progress, message):
                    nonlocal current_stage, total_chunks
                    
                    stage_map = {
                        'ingestion': (1, "Extract"),
                        'enrichment': (3, "Embed"),
                        'conflict': (3, "Embed"),
                        'decision': (4, "Index"),
                        'execution': (4, "Index"),
                        'complete': (4, "Index")
                    }
                    
                    if stage in stage_map:
                        current_stage, stage_name = stage_map[stage]
                        update_stages(current_stage)
                        stage_metric.metric("📊 Stage", f"{current_stage + 1}/5 {stage_name}")
                    
                    # Update progress
                    base = (file_idx / total_files)
                    file_portion = progress / total_files
                    total_progress = min(base + file_portion * 0.95, 0.99)
                    progress_bar.progress(total_progress, text=message)
                    status_placeholder.info(f"🔄 {message}")
                    
                    elapsed = time.time() - start_time
                    time_metric.metric("⏱️ Time", f"{elapsed:.1f}s")
                    progress_metric.metric("⚡ Progress", f"{int(total_progress * 100)}%")
                    
                    with details:
                        st.text(f"[{stage.upper()}] {message}")
                
                # Process document
                result = pipeline.process_document(
                    tmp_path,
                    progress_callback=progress_callback
                )
                
                # Update totals
                total_chunks += result['chunks_processed']
                for action, count in result['actions'].items():
                    if action in total_actions:
                        total_actions[action] += count
                
                chunks_metric.metric("📦 Chunks", total_chunks)
                
                if result['success']:
                    with details:
                        st.success(f"✅ {uploaded_file.name}: {result['chunks_processed']} chunks")
                else:
                    with details:
                        st.error(f"❌ {uploaded_file.name}: {'; '.join(result['errors'])}")
            
            finally:
                os.unlink(tmp_path)
        
        # Success!
        progress_bar.progress(1.0, text="✅ Complete!")
        update_stages(5)  # All complete
        status_placeholder.success("🎉 Processing Complete!")
        stage_metric.metric("📊 Stage", "✅ Done")
        progress_metric.metric("⚡ Progress", "100%")
        
        elapsed = time.time() - start_time
        time_metric.metric("⏱️ Time", f"{elapsed:.1f}s")
        
        # Success summary
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(16,185,129,0.2), rgba(59,130,246,0.1)); 
                    padding: 24px; border-radius: 16px; border: 1px solid #10b981; margin-top: 20px; text-align: center;">
            <h2 style="color: #10b981; margin: 0 0 16px 0;">🎉 Processing Complete!</h2>
            <div style="display: flex; justify-content: center; gap: 32px; flex-wrap: wrap;">
                <div style="text-align: center;">
                    <div style="font-size: 32px; font-weight: bold; color: #f8fafc;">{total_files}</div>
                    <div style="color: #94a3b8; font-size: 12px;">FILES</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 32px; font-weight: bold; color: #10b981;">{total_chunks}</div>
                    <div style="color: #94a3b8; font-size: 12px;">CHUNKS</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 32px; font-weight: bold; color: #8b5cf6;">{total_actions['INSERT']}</div>
                    <div style="color: #94a3b8; font-size: 12px;">INSERTED</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 32px; font-weight: bold; color: #f59e0b;">{elapsed:.1f}s</div>
                    <div style="color: #94a3b8; font-size: 12px;">TIME</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.balloons()
        st.cache_resource.clear()
        
    except Exception as e:
        status_placeholder.error(f"❌ Processing failed: {e}")
        import traceback
        with details:
            st.code(traceback.format_exc())


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
    
    /* ============================================
       PREMIUM PROGRESS VISUALIZATION CSS
       ============================================ */
    
    .premium-glass-panel {
        background: rgba(15, 23, 42, 0.8);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        padding: 24px;
        position: relative;
        overflow: hidden;
    }
    
    .premium-pipeline {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        padding: 20px 0;
    }
    
    .premium-stage {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 12px;
        flex: 1;
        max-width: 100px;
        position: relative;
        z-index: 2;
    }
    
    .premium-stage-icon {
        width: 64px;
        height: 64px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(15, 23, 42, 0.8);
        border: 2px solid rgba(255, 255, 255, 0.1);
        transition: all 0.4s ease;
    }
    
    .premium-stage-icon svg {
        width: 28px;
        height: 28px;
        color: #94a3b8;
    }
    
    .premium-stage-name {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #64748b;
    }
    
    .premium-stage.idle .premium-stage-icon {
        opacity: 0.4;
        filter: grayscale(100%);
    }
    
    .premium-stage.active .premium-stage-icon {
        border-color: var(--stage-color, #00d4ff);
        box-shadow: 0 0 30px color-mix(in srgb, var(--stage-color, #00d4ff) 50%, transparent);
        animation: stagePulse 2s ease-in-out infinite;
    }
    
    .premium-stage.active .premium-stage-icon svg {
        color: var(--stage-color, #00d4ff);
    }
    
    .premium-stage.active .premium-stage-name {
        color: var(--stage-color, #00d4ff);
    }
    
    .premium-stage.completed .premium-stage-icon {
        border-color: #10b981;
        background: rgba(16, 185, 129, 0.1);
    }
    
    .premium-stage.completed .premium-stage-icon svg {
        color: #10b981;
    }
    
    .premium-stage.completed .premium-stage-name {
        color: #10b981;
    }
    
    .premium-connector {
        flex: 1;
        height: 3px;
        background: rgba(255, 255, 255, 0.1);
        margin-top: 30px;
        border-radius: 2px;
        overflow: hidden;
    }
    
    .premium-connector-fill {
        height: 100%;
        width: 0%;
        background: linear-gradient(90deg, #00d4ff, #8b5cf6);
        transition: width 0.5s ease;
    }
    
    .premium-connector.active .premium-connector-fill {
        width: 50%;
        animation: connectorFlow 1.5s ease-in-out infinite;
    }
    
    .premium-connector.completed .premium-connector-fill {
        width: 100%;
        background: #10b981;
    }
    
    .premium-progress-container {
        margin: 24px 0;
        position: relative;
    }
    
    .premium-progress-bar {
        height: 8px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 4px;
        overflow: hidden;
    }
    
    .premium-progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #00d4ff, #8b5cf6, #ec4899);
        background-size: 200% 100%;
        border-radius: 4px;
        transition: width 0.3s ease;
        animation: gradientShift 3s ease infinite;
    }
    
    .premium-progress-glow {
        position: absolute;
        top: -10px;
        height: 28px;
        width: 100px;
        background: radial-gradient(ellipse, rgba(0, 212, 255, 0.4), transparent 70%);
        filter: blur(8px);
        pointer-events: none;
    }
    
    .premium-progress-percent {
        position: absolute;
        right: 0;
        top: -28px;
        font-size: 14px;
        font-weight: 700;
        color: #f8fafc;
    }
    
    .premium-metrics {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin: 20px 0;
    }
    
    .premium-metric-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    
    .premium-metric-icon {
        font-size: 20px;
        margin-bottom: 8px;
    }
    
    .premium-metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #f8fafc;
        line-height: 1;
        margin-bottom: 4px;
    }
    
    .premium-metric-label {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #64748b;
    }
    
    .premium-metric-card.stage .premium-metric-value { color: #00d4ff; }
    .premium-metric-card.progress .premium-metric-value { color: #8b5cf6; }
    .premium-metric-card.chunks .premium-metric-value { color: #10b981; }
    .premium-metric-card.time .premium-metric-value { color: #f59e0b; }
    
    .premium-status {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 20px;
    }
    
    .premium-status-indicator {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #00d4ff;
        animation: statusPulse 1.5s ease-in-out infinite;
    }
    
    .premium-status-text {
        font-size: 16px;
        font-weight: 500;
        color: #f8fafc;
    }
    
    .premium-eta {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        padding: 12px;
        background: rgba(0, 212, 255, 0.05);
        border-radius: 12px;
        margin-top: 16px;
    }
    
    .premium-eta-icon { font-size: 18px; }
    .premium-eta-text { font-size: 14px; color: #00d4ff; font-weight: 500; }
    
    .premium-success { text-align: center; padding: 40px 20px; }
    .premium-success-title { font-size: 24px; font-weight: 700; color: #10b981; margin-bottom: 8px; }
    .premium-success-subtitle { font-size: 14px; color: #94a3b8; }
    
    .premium-success-circle {
        stroke: #10b981;
        stroke-width: 3;
        fill: none;
        stroke-dasharray: 251;
        stroke-dashoffset: 251;
        animation: circleDrawn 0.6s ease forwards;
    }
    
    .premium-success-check {
        stroke: #10b981;
        stroke-width: 4;
        fill: none;
        stroke-linecap: round;
        stroke-dasharray: 50;
        stroke-dashoffset: 50;
        animation: checkDrawn 0.4s ease 0.5s forwards;
    }
    
    @keyframes stagePulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    @keyframes connectorFlow {
        0% { width: 30%; }
        50% { width: 70%; }
        100% { width: 30%; }
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    @keyframes statusPulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    @keyframes circleDrawn {
        100% { stroke-dashoffset: 0; }
    }
    
    @keyframes checkDrawn {
        100% { stroke-dashoffset: 0; }
    }
    
    @media (max-width: 640px) {
        .premium-pipeline { flex-direction: column; gap: 8px; }
        .premium-stage { flex-direction: row; max-width: 100%; }
        .premium-metrics { grid-template-columns: repeat(2, 1fr); }
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_rag_system():
    """Initialize and cache RAG system."""
    rag = SelfLearningRAG()
    # Try to load existing index, but don't fail if none exists
    if not rag.is_ready:
        try:
            rag.initialize()
        except Exception as e:
            # No documents to index yet - that's okay, user can upload
            print(f"Note: Could not initialize index: {e}")
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
        
        st.markdown("---")
        
        # Document Upload Section
        st.header("📤 Upload Documents")
        
        uploaded_files = st.file_uploader(
            "Add PDF documents",
            type=['pdf'],
            accept_multiple_files=True,
            help="Upload course materials to add to the knowledge base"
        )
        
        if uploaded_files:
            if st.button("📥 Process Uploads", use_container_width=True):
                process_uploaded_files(uploaded_files, rag)
        
        # Document Manager
        st.markdown("---")
        st.header("📚 Document Library")
        
        try:
            sources = rag.pipeline.retriever.vector_store.faiss_store.get_document_sources()
            if sources:
                for source in sources[:10]:  # Show top 10
                    with st.expander(f"📄 {source['filename']}", expanded=False):
                        st.caption(f"Chunks: {source['chunk_count']}")
                        st.caption(f"Pages: {len(source['pages'])}")
                        if st.button("🗑️ Remove", key=f"del_{source['filename']}", use_container_width=True):
                            # Remove document
                            rag.pipeline.retriever.vector_store.faiss_store.remove_documents(
                                source['chunk_indices'],
                                save_after=True
                            )
                            st.success(f"Removed {source['filename']}")
                            st.rerun()
            else:
                st.info("No documents indexed yet")
        except Exception as e:
            st.warning(f"Could not load document list: {e}")
    
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
                # Check if RAG system has documents
                if not rag.is_ready:
                    st.warning("⚠️ No documents indexed yet! Please upload PDF files using the sidebar first.")
                else:
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
