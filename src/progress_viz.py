"""
Progress Visualization Module
Implements progress tracking, ETA calculation, and visual components.
"""

import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable, Literal
from dataclasses import dataclass, field
from collections import deque
import threading


# =============================================================================
# Progress State Schema
# =============================================================================

@dataclass
class StageMetrics:
    """Stage-specific metrics."""
    items_processed: int = 0
    total_items: int = 0
    speed: float = 0.0  # items per second
    custom: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class ProgressState:
    """Complete progress state for tracking operations."""
    stage: str = ""
    stage_index: int = 0
    total_stages: int = 0
    progress_percent: float = 0.0
    status: Literal['idle', 'processing', 'success', 'error', 'warning'] = 'idle'
    message: str = ""
    eta_seconds: Optional[float] = None
    start_time: Optional[datetime] = None
    stage_start_time: Optional[datetime] = None
    metrics: StageMetrics = field(default_factory=StageMetrics)
    history: List[Dict[str, Any]] = field(default_factory=list)


# =============================================================================
# Stage Configuration
# =============================================================================

UPLOAD_STAGES = [
    {'name': 'Upload', 'icon': '📤', 'color': '#00d4ff', 'weight': 0.05},
    {'name': 'Extract', 'icon': '📄', 'color': '#7b2ff7', 'weight': 0.20},
    {'name': 'Chunk', 'icon': '✂️', 'color': '#ff6b6b', 'weight': 0.10},
    {'name': 'Embed', 'icon': '🧠', 'color': '#4ecdc4', 'weight': 0.50},
    {'name': 'Index', 'icon': '💾', 'color': '#ffe66d', 'weight': 0.10},
    {'name': 'Complete', 'icon': '✅', 'color': '#00ff88', 'weight': 0.05}
]

QUERY_STAGES = [
    {'name': 'Embedding', 'icon': '🔍', 'color': '#00d4ff'},
    {'name': 'Retrieval', 'icon': '🎯', 'color': '#7b2ff7'},
    {'name': 'Fusion', 'icon': '⚖️', 'color': '#ff6b6b'},
    {'name': 'Generation', 'icon': '🤖', 'color': '#4ecdc4'},
    {'name': 'Citations', 'icon': '📎', 'color': '#ffe66d'}
]


# =============================================================================
# ETA Calculator
# =============================================================================

class ETACalculator:
    """
    Calculates estimated time remaining using exponential moving average.
    """
    
    def __init__(self, smoothing_factor: float = 0.3):
        self.smoothing_factor = smoothing_factor
        self.speed_history: deque = deque(maxlen=10)
        self.current_speed: float = 0.0
        self.last_update: Optional[float] = None
        self.last_items: int = 0
    
    def update(self, items_done: int, total_items: int) -> Optional[float]:
        """
        Update ETA based on progress.
        
        Args:
            items_done: Number of items completed
            total_items: Total number of items
            
        Returns:
            Estimated seconds remaining, or None if not calculable
        """
        current_time = time.time()
        
        if self.last_update is not None and items_done > self.last_items:
            time_delta = current_time - self.last_update
            items_delta = items_done - self.last_items
            
            if time_delta > 0:
                instant_speed = items_delta / time_delta
                
                # Exponential moving average
                if self.current_speed == 0:
                    self.current_speed = instant_speed
                else:
                    self.current_speed = (
                        self.smoothing_factor * instant_speed + 
                        (1 - self.smoothing_factor) * self.current_speed
                    )
                
                self.speed_history.append(instant_speed)
        
        self.last_update = current_time
        self.last_items = items_done
        
        # Calculate ETA
        if self.current_speed > 0 and total_items > items_done:
            remaining_items = total_items - items_done
            return remaining_items / self.current_speed
        
        return None
    
    def reset(self):
        """Reset calculator for new task."""
        self.speed_history.clear()
        self.current_speed = 0.0
        self.last_update = None
        self.last_items = 0
    
    @staticmethod
    def format_eta(seconds: Optional[float]) -> str:
        """Format ETA as human-readable string."""
        if seconds is None:
            return "Calculating..."
        
        if seconds < 1:
            return "< 1s"
        elif seconds < 60:
            return f"{int(seconds)}s remaining"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s remaining"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m remaining"


# =============================================================================
# Progress Tracker
# =============================================================================

class ProgressTracker:
    """
    Tracks progress through multi-stage operations.
    Thread-safe and callback-enabled.
    """
    
    def __init__(
        self, 
        stages: List[Dict[str, Any]] = None,
        callback: Optional[Callable[[ProgressState], None]] = None
    ):
        self.stages = stages or UPLOAD_STAGES
        self.callback = callback
        self.state = ProgressState(total_stages=len(self.stages))
        self.eta_calculator = ETACalculator()
        self._lock = threading.Lock()
        
        # Debouncing
        self._last_callback_time = 0
        self._min_callback_interval = 0.2  # 200ms max 5 updates/sec
    
    def start_operation(self, message: str = "Starting..."):
        """Start a new operation from the beginning."""
        with self._lock:
            self.state = ProgressState(
                total_stages=len(self.stages),
                status='processing',
                message=message,
                start_time=datetime.now()
            )
            self.eta_calculator.reset()
            self._emit_callback()
    
    def start_stage(self, stage_name: str, total_items: int = 0, message: str = ""):
        """Start a new stage."""
        with self._lock:
            # Find stage index
            stage_idx = next(
                (i for i, s in enumerate(self.stages) if s['name'] == stage_name), 
                self.state.stage_index
            )
            
            self.state.stage = stage_name
            self.state.stage_index = stage_idx
            self.state.stage_start_time = datetime.now()
            self.state.status = 'processing'
            self.state.message = message or f"Processing {stage_name}..."
            self.state.metrics = StageMetrics(total_items=total_items)
            
            self.eta_calculator.reset()
            self._update_overall_progress()
            self._emit_callback()
    
    def update_progress(
        self, 
        items_done: int, 
        message: str = "",
        custom_metrics: Dict[str, Any] = None
    ):
        """Update progress within current stage."""
        with self._lock:
            self.state.metrics.items_processed = items_done
            
            if message:
                self.state.message = message
            
            if custom_metrics:
                self.state.metrics.custom.update(custom_metrics)
            
            # Calculate ETA
            if self.state.metrics.total_items > 0:
                eta = self.eta_calculator.update(
                    items_done, 
                    self.state.metrics.total_items
                )
                self.state.eta_seconds = eta
                self.state.metrics.speed = self.eta_calculator.current_speed
            
            self._update_overall_progress()
            self._emit_callback(debounced=True)
    
    def complete_stage(self, success: bool = True, message: str = ""):
        """Complete the current stage."""
        with self._lock:
            status = 'success' if success else 'error'
            
            # Add to history
            self.state.history.append({
                'stage': self.state.stage,
                'status': status,
                'duration': self._get_stage_duration(),
                'metrics': {
                    'items': self.state.metrics.items_processed,
                    'speed': self.state.metrics.speed
                }
            })
            
            self.state.status = status
            self.state.message = message or f"{self.state.stage} complete"
            
            self._update_overall_progress()
            self._emit_callback()
    
    def complete_operation(self, success: bool = True, message: str = ""):
        """Complete the entire operation."""
        with self._lock:
            self.state.status = 'success' if success else 'error'
            self.state.progress_percent = 100.0 if success else self.state.progress_percent
            self.state.message = message or ("Complete!" if success else "Failed")
            self.state.eta_seconds = None
            self._emit_callback()
    
    def set_error(self, message: str):
        """Set error state."""
        with self._lock:
            self.state.status = 'error'
            self.state.message = message
            self._emit_callback()
    
    def get_state(self) -> ProgressState:
        """Get current progress state snapshot."""
        with self._lock:
            return ProgressState(**self.state.__dict__)
    
    def _update_overall_progress(self):
        """Calculate overall progress percentage."""
        # Calculate based on stage weights
        completed_weight = sum(
            s['weight'] for i, s in enumerate(self.stages) 
            if i < self.state.stage_index
        )
        
        # Add current stage partial progress
        if self.state.stage_index < len(self.stages):
            current_stage = self.stages[self.state.stage_index]
            if self.state.metrics.total_items > 0:
                stage_progress = (
                    self.state.metrics.items_processed / 
                    self.state.metrics.total_items
                )
            else:
                stage_progress = 0
            
            completed_weight += current_stage['weight'] * stage_progress
        
        self.state.progress_percent = min(completed_weight * 100, 100)
    
    def _get_stage_duration(self) -> float:
        """Get duration of current stage in seconds."""
        if self.state.stage_start_time:
            return (datetime.now() - self.state.stage_start_time).total_seconds()
        return 0
    
    def _emit_callback(self, debounced: bool = False):
        """Emit callback with debouncing."""
        if self.callback is None:
            return
        
        current_time = time.time()
        
        if debounced:
            if current_time - self._last_callback_time < self._min_callback_interval:
                return
        
        self._last_callback_time = current_time
        
        try:
            self.callback(self.state)
        except Exception as e:
            # Don't let callback errors crash the main process
            print(f"Warning: Progress callback error: {e}")


# =============================================================================
# Glassmorphism CSS
# =============================================================================

GLASSMORPHISM_CSS = """
<style>
/* Glassmorphism Variables */
:root {
    --glass-bg: rgba(255, 255, 255, 0.05);
    --glass-bg-hover: rgba(255, 255, 255, 0.08);
    --glass-border: rgba(255, 255, 255, 0.1);
    --glass-blur: 10px;
    --accent-primary: #00d4ff;
    --accent-secondary: #7b2ff7;
    --success-color: #00ff88;
    --error-color: #ff4444;
    --warning-color: #ffaa00;
}

/* Glass Panel Base */
.glass-panel {
    background: var(--glass-bg);
    backdrop-filter: blur(var(--glass-blur));
    -webkit-backdrop-filter: blur(var(--glass-blur));
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    transition: all 0.3s ease;
}

.glass-panel:hover {
    background: var(--glass-bg-hover);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
}

/* Progress Pipeline Container */
.progress-pipeline {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px;
    gap: 8px;
    background: var(--glass-bg);
    border-radius: 16px;
    margin: 16px 0;
}

/* Stage Indicator */
.stage-indicator {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    flex: 1;
    max-width: 100px;
}

.stage-icon {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    background: rgba(255, 255, 255, 0.05);
    border: 2px solid rgba(255, 255, 255, 0.1);
    transition: all 0.3s ease;
}

.stage-indicator.idle .stage-icon {
    opacity: 0.4;
    filter: grayscale(100%);
}

.stage-indicator.active .stage-icon {
    border-color: var(--accent-primary);
    box-shadow: 0 0 20px var(--accent-primary);
    animation: pulse 1.5s ease-in-out infinite;
}

.stage-indicator.completed .stage-icon {
    border-color: var(--success-color);
    background: rgba(0, 255, 136, 0.1);
}

.stage-indicator.error .stage-icon {
    border-color: var(--error-color);
    animation: shake 0.5s ease-in-out;
}

.stage-name {
    font-size: 12px;
    color: #94A3B8;
    text-align: center;
}

.stage-indicator.active .stage-name {
    color: var(--accent-primary);
    font-weight: 600;
}

/* Stage Connector */
.stage-connector {
    flex: 0.5;
    height: 2px;
    background: rgba(255, 255, 255, 0.1);
    position: relative;
    overflow: hidden;
}

.stage-connector.active::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    width: 100%;
    background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
    animation: progressFlow 1s ease-in-out infinite;
}

.stage-connector.completed {
    background: var(--success-color);
}

/* Progress Bar */
.progress-bar-container {
    width: 100%;
    height: 8px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    overflow: hidden;
    margin: 16px 0;
}

.progress-bar-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
    border-radius: 4px;
    transition: width 0.3s ease;
    position: relative;
}

.progress-bar-fill::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(
        90deg, 
        transparent, 
        rgba(255, 255, 255, 0.3), 
        transparent
    );
    animation: shimmer 1.5s infinite;
}

/* Metrics Display */
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 12px;
    margin: 16px 0;
}

.metric-card {
    background: var(--glass-bg);
    border-radius: 12px;
    padding: 16px;
    text-align: center;
    border: 1px solid var(--glass-border);
}

.metric-value {
    font-size: 24px;
    font-weight: bold;
    color: #F8FAFC;
    margin-bottom: 4px;
}

.metric-label {
    font-size: 12px;
    color: #94A3B8;
}

/* ETA Display */
.eta-display {
    text-align: center;
    padding: 12px;
    color: var(--accent-primary);
    font-size: 14px;
}

/* Animations */
@keyframes pulse {
    0%, 100% { transform: scale(1); box-shadow: 0 0 20px var(--accent-primary); }
    50% { transform: scale(1.05); box-shadow: 0 0 30px var(--accent-primary); }
}

@keyframes shake {
    0%, 100% { transform: translateX(0); }
    25% { transform: translateX(-5px); }
    75% { transform: translateX(5px); }
}

@keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
}

@keyframes progressFlow {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
}

/* Success Animation */
.success-checkmark {
    width: 80px;
    height: 80px;
    margin: 20px auto;
}

.checkmark-circle {
    stroke: var(--success-color);
    stroke-width: 2;
    stroke-dasharray: 166;
    stroke-dashoffset: 166;
    animation: stroke 0.6s cubic-bezier(0.65, 0, 0.45, 1) forwards;
}

.checkmark-check {
    stroke: var(--success-color);
    stroke-width: 3;
    stroke-linecap: round;
    stroke-dasharray: 48;
    stroke-dashoffset: 48;
    animation: stroke 0.3s cubic-bezier(0.65, 0, 0.45, 1) 0.6s forwards;
}

@keyframes stroke {
    100% { stroke-dashoffset: 0; }
}
</style>
"""


# =============================================================================
# Progress Display Component
# =============================================================================

def render_progress_html(state: ProgressState, stages: List[Dict] = None) -> str:
    """Render progress visualization as HTML."""
    stages = stages or UPLOAD_STAGES
    
    # Build stage indicators HTML
    stage_html = ""
    for i, stage in enumerate(stages[:-1]):  # Exclude 'Complete' stage
        if i < state.stage_index:
            status = "completed"
        elif i == state.stage_index:
            status = "active" if state.status == 'processing' else state.status
        else:
            status = "idle"
        
        stage_html += f"""
        <div class="stage-indicator {status}">
            <div class="stage-icon">{stage['icon']}</div>
            <div class="stage-name">{stage['name']}</div>
        </div>
        """
        
        # Add connector (except after last stage)
        if i < len(stages) - 2:
            connector_status = "completed" if i < state.stage_index else ("active" if i == state.stage_index else "")
            stage_html += f'<div class="stage-connector {connector_status}"></div>'
    
    # Build metrics HTML
    metrics_html = f"""
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-value">{state.stage_index + 1}/{len(stages) - 1}</div>
            <div class="metric-label">Stage</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{state.progress_percent:.0f}%</div>
            <div class="metric-label">Progress</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{state.metrics.items_processed}</div>
            <div class="metric-label">Items</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{state.metrics.speed:.1f}/s</div>
            <div class="metric-label">Speed</div>
        </div>
    </div>
    """
    
    # ETA
    eta_text = ETACalculator.format_eta(state.eta_seconds)
    
    # Full HTML
    html = f"""
    <div class="glass-panel" style="padding: 24px; margin: 16px 0;">
        <div style="margin-bottom: 16px; font-size: 16px; color: #F8FAFC;">
            <strong>{state.message}</strong>
        </div>
        
        <div class="progress-pipeline">
            {stage_html}
        </div>
        
        <div class="progress-bar-container">
            <div class="progress-bar-fill" style="width: {state.progress_percent}%"></div>
        </div>
        
        {metrics_html}
        
        <div class="eta-display">⏱️ {eta_text}</div>
    </div>
    """
    
    return html


def render_success_animation() -> str:
    """Render success checkmark animation."""
    return """
    <div class="glass-panel" style="padding: 40px; text-align: center; margin: 16px 0;">
        <svg class="success-checkmark" viewBox="0 0 52 52">
            <circle class="checkmark-circle" cx="26" cy="26" r="25" fill="none"/>
            <path class="checkmark-check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
        </svg>
        <div style="color: var(--success-color); font-size: 24px; font-weight: bold; margin-top: 16px;">
            Processing Complete!
        </div>
    </div>
    """


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'ProgressState',
    'StageMetrics', 
    'ProgressTracker',
    'ETACalculator',
    'UPLOAD_STAGES',
    'QUERY_STAGES',
    'GLASSMORPHISM_CSS',
    'render_progress_html',
    'render_success_animation'
]
