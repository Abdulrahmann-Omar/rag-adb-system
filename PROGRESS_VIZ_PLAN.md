# Phase 2: Progress Visualization - Detailed Implementation Plan

## 2.1 Progress Infrastructure (1.5 hours)

### 2.1.1 Progress State Management (30 min)
**Priority**: P0 | **Dependencies**: None

#### Progress State Schema
```python
ProgressState = {
    'stage': str,           # current stage name
    'stage_index': int,     # 0-based index
    'total_stages': int,
    'progress_percent': float,  # 0-100
    'status': Literal['idle', 'processing', 'success', 'error', 'warning'],
    'message': str,         # user-facing status message
    'eta_seconds': Optional[float],
    'start_time': datetime,
    'metrics': dict         # stage-specific metrics
}
```

#### Stage-Specific Metrics
| Stage | Metrics |
|-------|---------|
| Upload | file_name, file_size_mb, upload_speed_mbps |
| Extraction | pages_processed, total_pages, current_page |
| Chunking | chunks_created, avg_chunk_size, total_chars |
| Embedding | batches_processed, total_batches, embeddings_generated |
| Indexing | vectors_added, index_size_mb, merge_status |

#### Tasks
- [/] Design ProgressState dataclass
- [ ] Create ProgressTracker class
- [ ] Implement ETACalculator class
- [ ] Add ETA formatting utility

---

### 2.1.2 Progress Update Callbacks (30 min)
**Priority**: P0 | **Dependencies**: 2.1.1

- [ ] Add callbacks to PDF extraction (per page)
- [ ] Add callbacks to chunking (per batch)
- [ ] Add callbacks to embedding (per batch)
- [ ] Add callbacks to FAISS indexing
- [ ] Implement callback debouncing (max 5/sec)

---

### 2.1.3 Real-Time Update Mechanism (30 min)
**Priority**: P1 | **Dependencies**: 2.1.1, 2.1.2

- [ ] Create ProgressDisplay class with auto-refresh
- [ ] Implement background task handler
- [ ] Build progress event emitter

---

## 2.2 Visual Components (2 hours)

### 2.2.1 Glassmorphism CSS Framework (30 min)
**Priority**: P1

#### CSS Variables
```css
:root {
    --glass-bg: rgba(255, 255, 255, 0.05);
    --glass-border: rgba(255, 255, 255, 0.1);
    --glass-blur: 10px;
    --accent-primary: #00d4ff;
    --accent-secondary: #7b2ff7;
    --success-glow: #00ff88;
    --error-glow: #ff4444;
}
```

- [/] Create glass panel classes
- [ ] Add gradient backgrounds
- [ ] Design component library

---

### 2.2.2 Multi-Stage Progress Bar (45 min)
**Priority**: P0

#### Stage Configuration
```python
STAGES = [
    {'name': 'Upload', 'icon': '📤', 'color': '#00d4ff'},
    {'name': 'Extract', 'icon': '📄', 'color': '#7b2ff7'},
    {'name': 'Chunk', 'icon': '✂️', 'color': '#ff6b6b'},
    {'name': 'Embed', 'icon': '🧠', 'color': '#4ecdc4'},
    {'name': 'Index', 'icon': '💾', 'color': '#ffe66d'}
]
```

- [ ] Build HTML/CSS progress bar
- [ ] Create MultiStageProgress Python class
- [ ] Add percentage and ETA display
- [ ] Implement accessibility (ARIA labels)

---

### 2.2.3 Animated Stage Indicators (30 min)
**Priority**: P1

- [ ] Create loading spinner variants
- [ ] Build success checkmark animation
- [ ] Create error shake animation
- [ ] Add transition animations

---

### 2.2.4 Real-Time Metrics Display (15 min)
**Priority**: P1

- [ ] Design metrics card layout
- [ ] Implement number counting animation
- [ ] Add visual indicators (progress bars, colors)

---

## 2.3 Query Journey Visualization (1 hour)

### 2.3.1 Query Pipeline Timeline (30 min)
**Priority**: P1

#### Query Stages
| Stage | Icon | Description |
|-------|------|-------------|
| Query Embedding | 🔍 | Encode query to vector |
| Semantic Search | 🎯 | FAISS similarity search |
| BM25 Search | 📊 | Keyword-based search |
| Score Fusion | ⚖️ | Combine hybrid scores |
| LLM Generation | 🤖 | Generate response |
| Citation Extraction | 📎 | Extract source references |

- [ ] Create horizontal timeline HTML
- [ ] Implement stage timing tracker
- [ ] Add stage detail tooltips

---

### 2.3.2 Retrieved Documents Preview (20 min)
**Priority**: P1

- [ ] Design document card layout
- [ ] Implement snippet extraction with highlights
- [ ] Create relevance score visualization
- [ ] Build expandable view

---

### 2.3.3 Success/Error Animations (10 min)
**Priority**: P2

- [ ] Create success animation library
- [ ] Build error animation set
- [ ] Implement warning states

---

## Estimated Timeline
| Section | Time |
|---------|------|
| 2.1 Progress Infrastructure | 1.5h |
| 2.2 Visual Components | 2h |
| 2.3 Query Journey | 1h |
| **Total** | **4.5h** |
