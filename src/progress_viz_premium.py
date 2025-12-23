"""
Premium Progress Visualization Module
Stunning visual feedback for multi-stage operations with glassmorphism design.
"""

import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Literal
from dataclasses import dataclass, field


# =============================================================================
# Premium CSS Framework
# =============================================================================

PREMIUM_CSS = """
<style>
/* ============================================
   PREMIUM PROGRESS VISUALIZATION CSS
   Glassmorphism + Animated Components
   ============================================ */

/* CSS Variables */
:root {
    /* Colors */
    --glass-bg: rgba(15, 23, 42, 0.8);
    --glass-border: rgba(255, 255, 255, 0.1);
    --glass-highlight: rgba(255, 255, 255, 0.05);
    
    /* Accent Colors */
    --accent-cyan: #00d4ff;
    --accent-purple: #8b5cf6;
    --accent-pink: #ec4899;
    --accent-green: #10b981;
    --accent-red: #ef4444;
    --accent-yellow: #f59e0b;
    
    /* Stage Colors */
    --stage-upload: #00d4ff;
    --stage-extract: #8b5cf6;
    --stage-chunk: #ec4899;
    --stage-embed: #10b981;
    --stage-index: #f59e0b;
    
    /* Text */
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    
    /* Spacing */
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --radius-xl: 24px;
}

/* ============================================
   GLASS PANEL COMPONENT
   ============================================ */

.premium-glass-panel {
    background: var(--glass-bg);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-xl);
    box-shadow: 
        0 25px 50px -12px rgba(0, 0, 0, 0.5),
        inset 0 1px 0 var(--glass-highlight);
    padding: 24px;
    position: relative;
    overflow: hidden;
}

.premium-glass-panel::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, 
        transparent 0%, 
        rgba(255,255,255,0.2) 50%, 
        transparent 100%
    );
}

/* ============================================
   STAGE PIPELINE CONTAINER
   ============================================ */

.premium-pipeline {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    padding: 20px 0;
    position: relative;
}

/* ============================================
   STAGE INDICATOR COMPONENT
   ============================================ */

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
    position: relative;
    background: var(--glass-bg);
    border: 2px solid var(--glass-border);
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.premium-stage-icon svg {
    width: 28px;
    height: 28px;
    transition: all 0.3s ease;
}

.premium-stage-name {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--text-muted);
    transition: all 0.3s ease;
}

/* Stage States */

/* Idle */
.premium-stage.idle .premium-stage-icon {
    opacity: 0.4;
    filter: grayscale(100%);
}

.premium-stage.idle .premium-stage-icon svg {
    opacity: 0.5;
}

/* Active */
.premium-stage.active .premium-stage-icon {
    border-color: var(--stage-color, var(--accent-cyan));
    box-shadow: 
        0 0 30px color-mix(in srgb, var(--stage-color, var(--accent-cyan)) 50%, transparent),
        0 0 60px color-mix(in srgb, var(--stage-color, var(--accent-cyan)) 25%, transparent);
    animation: stagePulse 2s ease-in-out infinite;
}

.premium-stage.active .premium-stage-icon svg {
    color: var(--stage-color, var(--accent-cyan));
    filter: drop-shadow(0 0 8px var(--stage-color, var(--accent-cyan)));
}

.premium-stage.active .premium-stage-name {
    color: var(--stage-color, var(--accent-cyan));
}

/* Completed */
.premium-stage.completed .premium-stage-icon {
    border-color: var(--accent-green);
    background: rgba(16, 185, 129, 0.1);
}

.premium-stage.completed .premium-stage-icon svg {
    color: var(--accent-green);
}

.premium-stage.completed .premium-stage-name {
    color: var(--accent-green);
}

/* Error */
.premium-stage.error .premium-stage-icon {
    border-color: var(--accent-red);
    animation: stageShake 0.5s ease-in-out;
}

.premium-stage.error .premium-stage-icon svg {
    color: var(--accent-red);
}

/* ============================================
   STAGE CONNECTOR
   ============================================ */

.premium-connector {
    flex: 1;
    height: 3px;
    background: var(--glass-border);
    position: relative;
    margin-top: 30px;
    border-radius: 2px;
    overflow: hidden;
}

.premium-connector-fill {
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    width: 0%;
    background: linear-gradient(90deg, var(--accent-cyan), var(--accent-purple));
    border-radius: 2px;
    transition: width 0.5s ease;
}

.premium-connector.active .premium-connector-fill {
    width: 50%;
    animation: connectorFlow 1.5s ease-in-out infinite;
}

.premium-connector.completed .premium-connector-fill {
    width: 100%;
    background: var(--accent-green);
}

/* ============================================
   PREMIUM PROGRESS BAR
   ============================================ */

.premium-progress-container {
    margin: 24px 0;
    position: relative;
}

.premium-progress-bar {
    height: 8px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
    overflow: hidden;
    position: relative;
}

.premium-progress-fill {
    height: 100%;
    background: linear-gradient(90deg, 
        var(--accent-cyan) 0%, 
        var(--accent-purple) 50%, 
        var(--accent-pink) 100%
    );
    background-size: 200% 100%;
    border-radius: 4px;
    transition: width 0.3s ease;
    position: relative;
    animation: gradientShift 3s ease infinite;
}

.premium-progress-fill::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(
        90deg,
        transparent 0%,
        rgba(255, 255, 255, 0.4) 50%,
        transparent 100%
    );
    animation: shimmer 2s ease-in-out infinite;
}

.premium-progress-glow {
    position: absolute;
    top: -10px;
    height: 28px;
    width: 100px;
    background: radial-gradient(
        ellipse at center,
        rgba(0, 212, 255, 0.4) 0%,
        transparent 70%
    );
    filter: blur(8px);
    pointer-events: none;
    transition: left 0.3s ease;
}

.premium-progress-percent {
    position: absolute;
    right: 0;
    top: -28px;
    font-size: 14px;
    font-weight: 700;
    color: var(--text-primary);
    text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
}

/* ============================================
   METRICS GRID
   ============================================ */

.premium-metrics {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin: 20px 0;
}

.premium-metric-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-md);
    padding: 16px;
    text-align: center;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

.premium-metric-card:hover {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(255, 255, 255, 0.2);
    transform: translateY(-2px);
}

.premium-metric-icon {
    font-size: 20px;
    margin-bottom: 8px;
    opacity: 0.8;
}

.premium-metric-value {
    font-size: 28px;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1;
    margin-bottom: 4px;
}

.premium-metric-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--text-muted);
}

/* Metric card accent colors */
.premium-metric-card.stage .premium-metric-value { color: var(--accent-cyan); }
.premium-metric-card.progress .premium-metric-value { color: var(--accent-purple); }
.premium-metric-card.chunks .premium-metric-value { color: var(--accent-green); }
.premium-metric-card.time .premium-metric-value { color: var(--accent-yellow); }

/* ============================================
   STATUS MESSAGE
   ============================================ */

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
    background: var(--accent-cyan);
    animation: statusPulse 1.5s ease-in-out infinite;
}

.premium-status-text {
    font-size: 16px;
    font-weight: 500;
    color: var(--text-primary);
}

/* ============================================
   ETA DISPLAY - ENHANCED
   ============================================ */

.premium-eta {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 16px;
    padding: 16px 24px;
    background: linear-gradient(135deg, rgba(0, 212, 255, 0.08) 0%, rgba(139, 92, 246, 0.08) 100%);
    border: 1px solid rgba(0, 212, 255, 0.2);
    border-radius: var(--radius-lg);
    margin-top: 20px;
    position: relative;
    overflow: hidden;
}

.premium-eta::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
    animation: etaShimmer 3s ease-in-out infinite;
}

@keyframes etaShimmer {
    0% { left: -100%; }
    100% { left: 100%; }
}

.premium-eta-clock {
    width: 40px;
    height: 40px;
    position: relative;
}

.premium-eta-clock svg {
    width: 100%;
    height: 100%;
}

.clock-face {
    fill: none;
    stroke: rgba(0, 212, 255, 0.3);
    stroke-width: 2;
}

.clock-hand {
    fill: none;
    stroke: var(--accent-cyan);
    stroke-width: 2;
    stroke-linecap: round;
    transform-origin: center;
    animation: clockSpin 2s linear infinite;
}

@keyframes clockSpin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.premium-eta-content {
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.premium-eta-time {
    font-size: 20px;
    font-weight: 700;
    color: var(--text-primary);
    text-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
}

.premium-eta-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--text-muted);
}

.premium-eta-ring {
    width: 40px;
    height: 40px;
}

.eta-ring-bg {
    fill: none;
    stroke: rgba(255, 255, 255, 0.1);
    stroke-width: 3;
}

.eta-ring-progress {
    fill: none;
    stroke: var(--accent-cyan);
    stroke-width: 3;
    stroke-linecap: round;
    transform: rotate(-90deg);
    transform-origin: center;
    transition: stroke-dashoffset 0.5s ease;
}

/* ============================================
   SUCCESS CELEBRATION
   ============================================ */

.premium-success {
    text-align: center;
    padding: 40px 20px;
}

.premium-success-icon {
    width: 80px;
    height: 80px;
    margin: 0 auto 20px;
    position: relative;
}

.premium-success-circle {
    stroke: var(--accent-green);
    stroke-width: 3;
    fill: none;
    stroke-dasharray: 251;
    stroke-dashoffset: 251;
    animation: circleDrawn 0.6s ease forwards;
}

.premium-success-check {
    stroke: var(--accent-green);
    stroke-width: 4;
    fill: none;
    stroke-linecap: round;
    stroke-linejoin: round;
    stroke-dasharray: 50;
    stroke-dashoffset: 50;
    animation: checkDrawn 0.4s ease 0.5s forwards;
}

.premium-success-title {
    font-size: 24px;
    font-weight: 700;
    color: var(--accent-green);
    margin-bottom: 8px;
    text-shadow: 0 0 30px rgba(16, 185, 129, 0.5);
}

.premium-success-subtitle {
    font-size: 14px;
    color: var(--text-secondary);
}

/* ============================================
   ANIMATIONS
   ============================================ */

@keyframes stagePulse {
    0%, 100% { 
        transform: scale(1);
        box-shadow: 
            0 0 30px color-mix(in srgb, var(--stage-color, var(--accent-cyan)) 50%, transparent),
            0 0 60px color-mix(in srgb, var(--stage-color, var(--accent-cyan)) 25%, transparent);
    }
    50% { 
        transform: scale(1.05);
        box-shadow: 
            0 0 40px color-mix(in srgb, var(--stage-color, var(--accent-cyan)) 60%, transparent),
            0 0 80px color-mix(in srgb, var(--stage-color, var(--accent-cyan)) 35%, transparent);
    }
}

@keyframes stageShake {
    0%, 100% { transform: translateX(0); }
    20% { transform: translateX(-6px); }
    40% { transform: translateX(6px); }
    60% { transform: translateX(-4px); }
    80% { transform: translateX(4px); }
}

@keyframes connectorFlow {
    0% { width: 30%; opacity: 0.5; }
    50% { width: 70%; opacity: 1; }
    100% { width: 30%; opacity: 0.5; }
}

@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

@keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(200%); }
}

@keyframes statusPulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(0.9); }
}

@keyframes circleDrawn {
    100% { stroke-dashoffset: 0; }
}

@keyframes checkDrawn {
    100% { stroke-dashoffset: 0; }
}

/* ============================================
   RESPONSIVE DESIGN
   ============================================ */

@media (max-width: 640px) {
    .premium-pipeline {
        flex-direction: column;
        gap: 8px;
    }
    
    .premium-stage {
        flex-direction: row;
        max-width: 100%;
        justify-content: flex-start;
        gap: 16px;
    }
    
    .premium-stage-icon {
        width: 48px;
        height: 48px;
    }
    
    .premium-connector {
        width: 3px;
        height: 24px;
        margin: 0 0 0 22px;
    }
    
    .premium-metrics {
        grid-template-columns: repeat(2, 1fr);
    }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
    }
}
</style>
"""


# =============================================================================
# Animated SVG Icons
# =============================================================================

STAGE_ICONS = {
    'upload': '''
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" y1="3" x2="12" y2="15">
                <animate attributeName="y2" values="15;11;15" dur="1s" repeatCount="indefinite"/>
            </line>
        </svg>
    ''',
    'extract': '''
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13">
                <animate attributeName="opacity" values="1;0.3;1" dur="1.5s" repeatCount="indefinite"/>
            </line>
            <line x1="16" y1="17" x2="8" y2="17">
                <animate attributeName="opacity" values="0.3;1;0.3" dur="1.5s" repeatCount="indefinite"/>
            </line>
        </svg>
    ''',
    'chunk': '''
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="6" cy="6" r="3">
                <animate attributeName="r" values="3;3.5;3" dur="0.8s" repeatCount="indefinite"/>
            </circle>
            <circle cx="18" cy="6" r="3">
                <animate attributeName="r" values="3;3.5;3" dur="0.8s" repeatCount="indefinite" begin="0.2s"/>
            </circle>
            <circle cx="6" cy="18" r="3">
                <animate attributeName="r" values="3;3.5;3" dur="0.8s" repeatCount="indefinite" begin="0.4s"/>
            </circle>
            <circle cx="18" cy="18" r="3">
                <animate attributeName="r" values="3;3.5;3" dur="0.8s" repeatCount="indefinite" begin="0.6s"/>
            </circle>
            <line x1="9" y1="6" x2="15" y2="6" stroke-dasharray="2 2"/>
            <line x1="6" y1="9" x2="6" y2="15" stroke-dasharray="2 2"/>
            <line x1="18" y1="9" x2="18" y2="15" stroke-dasharray="2 2"/>
            <line x1="9" y1="18" x2="15" y2="18" stroke-dasharray="2 2"/>
        </svg>
    ''',
    'embed': '''
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="3">
                <animate attributeName="r" values="3;4;3" dur="1.5s" repeatCount="indefinite"/>
            </circle>
            <circle cx="12" cy="4" r="2"/>
            <circle cx="20" cy="12" r="2"/>
            <circle cx="12" cy="20" r="2"/>
            <circle cx="4" cy="12" r="2"/>
            <line x1="12" y1="7" x2="12" y2="9" stroke-opacity="0.5">
                <animate attributeName="stroke-opacity" values="0.5;1;0.5" dur="1s" repeatCount="indefinite"/>
            </line>
            <line x1="15" y1="12" x2="18" y2="12" stroke-opacity="0.5">
                <animate attributeName="stroke-opacity" values="0.5;1;0.5" dur="1s" repeatCount="indefinite" begin="0.25s"/>
            </line>
            <line x1="12" y1="15" x2="12" y2="18" stroke-opacity="0.5">
                <animate attributeName="stroke-opacity" values="0.5;1;0.5" dur="1s" repeatCount="indefinite" begin="0.5s"/>
            </line>
            <line x1="6" y1="12" x2="9" y2="12" stroke-opacity="0.5">
                <animate attributeName="stroke-opacity" values="0.5;1;0.5" dur="1s" repeatCount="indefinite" begin="0.75s"/>
            </line>
        </svg>
    ''',
    'index': '''
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <ellipse cx="12" cy="5" rx="9" ry="3"/>
            <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
            <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5">
                <animate attributeName="stroke-dasharray" values="0 100;100 0" dur="2s" repeatCount="indefinite"/>
            </path>
        </svg>
    ''',
    'complete': '''
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
        </svg>
    '''
}

STAGE_COLORS = {
    'upload': '#00d4ff',
    'extract': '#8b5cf6', 
    'chunk': '#ec4899',
    'embed': '#10b981',
    'index': '#f59e0b',
    'complete': '#10b981'
}


# =============================================================================
# Premium Stage Configuration
# =============================================================================

PREMIUM_STAGES = [
    {'name': 'Upload', 'key': 'upload', 'icon': '📤', 'weight': 0.05},
    {'name': 'Extract', 'key': 'extract', 'icon': '📄', 'weight': 0.20},
    {'name': 'Chunk', 'key': 'chunk', 'icon': '✂️', 'weight': 0.10},
    {'name': 'Embed', 'key': 'embed', 'icon': '🧠', 'weight': 0.50},
    {'name': 'Index', 'key': 'index', 'icon': '💾', 'weight': 0.15}
]


# =============================================================================
# Render Functions
# =============================================================================

def render_premium_progress(
    current_stage: int,
    progress_percent: float,
    message: str,
    metrics: Dict[str, Any],
    eta_text: str = "Calculating..."
) -> str:
    """Render the premium progress visualization."""
    
    stages_html = ""
    
    for i, stage in enumerate(PREMIUM_STAGES):
        # Determine stage state
        if i < current_stage:
            state = "completed"
        elif i == current_stage:
            state = "active"
        else:
            state = "idle"
        
        color = STAGE_COLORS.get(stage['key'], '#00d4ff')
        icon_svg = STAGE_ICONS.get(stage['key'], '')
        
        stages_html += f'''
        <div class="premium-stage {state}" style="--stage-color: {color};">
            <div class="premium-stage-icon" style="--stage-color: {color};">
                {icon_svg}
            </div>
            <div class="premium-stage-name">{stage['name']}</div>
        </div>
        '''
        
        # Add connector (except after last)
        if i < len(PREMIUM_STAGES) - 1:
            conn_state = "completed" if i < current_stage else ("active" if i == current_stage else "")
            stages_html += f'''
            <div class="premium-connector {conn_state}">
                <div class="premium-connector-fill"></div>
            </div>
            '''
    
    # Metrics
    stage_display = f"{current_stage + 1}/{len(PREMIUM_STAGES)}"
    chunks = metrics.get('chunks', 0)
    elapsed = metrics.get('elapsed', 0)
    
    html = f'''
    <div class="premium-glass-panel">
        <!-- Status -->
        <div class="premium-status">
            <div class="premium-status-indicator"></div>
            <div class="premium-status-text">{message}</div>
        </div>
        
        <!-- Stage Pipeline -->
        <div class="premium-pipeline">
            {stages_html}
        </div>
        
        <!-- Progress Bar -->
        <div class="premium-progress-container">
            <div class="premium-progress-percent">{progress_percent:.0f}%</div>
            <div class="premium-progress-bar">
                <div class="premium-progress-fill" style="width: {progress_percent}%;"></div>
            </div>
            <div class="premium-progress-glow" style="left: calc({progress_percent}% - 50px);"></div>
        </div>
        
        <!-- Metrics -->
        <div class="premium-metrics">
            <div class="premium-metric-card stage">
                <div class="premium-metric-icon">📊</div>
                <div class="premium-metric-value">{stage_display}</div>
                <div class="premium-metric-label">Stage</div>
            </div>
            <div class="premium-metric-card progress">
                <div class="premium-metric-icon">⚡</div>
                <div class="premium-metric-value">{progress_percent:.0f}%</div>
                <div class="premium-metric-label">Progress</div>
            </div>
            <div class="premium-metric-card chunks">
                <div class="premium-metric-icon">📦</div>
                <div class="premium-metric-value">{chunks}</div>
                <div class="premium-metric-label">Chunks</div>
            </div>
            <div class="premium-metric-card time">
                <div class="premium-metric-icon">⏱️</div>
                <div class="premium-metric-value">{elapsed:.1f}s</div>
                <div class="premium-metric-label">Elapsed</div>
            </div>
        </div>
        
        <!-- ETA Enhanced -->
        <div class="premium-eta">
            <div class="premium-eta-clock">
                <svg viewBox="0 0 40 40">
                    <circle class="clock-face" cx="20" cy="20" r="18"/>
                    <line class="clock-hand" x1="20" y1="20" x2="20" y2="8"/>
                </svg>
            </div>
            <div class="premium-eta-content">
                <div class="premium-eta-time">{eta_text}</div>
                <div class="premium-eta-label">Estimated Time</div>
            </div>
            <svg class="premium-eta-ring" viewBox="0 0 40 40">
                <circle class="eta-ring-bg" cx="20" cy="20" r="16"/>
                <circle class="eta-ring-progress" cx="20" cy="20" r="16" 
                    stroke-dasharray="100" 
                    stroke-dashoffset="{100 - progress_percent}"/>
            </svg>
        </div>
    </div>
    '''
    
    return html


def render_premium_success(
    total_files: int,
    total_chunks: int,
    elapsed: float,
    actions: Dict[str, int]
) -> str:
    """Render the premium success celebration with confetti."""
    
    # Confetti JavaScript
    confetti_js = '''
    <script>
    (function() {
        // Create canvas for confetti
        const canvas = document.createElement('canvas');
        canvas.id = 'confetti-canvas';
        canvas.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:9999;';
        document.body.appendChild(canvas);
        
        const ctx = canvas.getContext('2d');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        
        const particles = [];
        const colors = ['#00d4ff', '#8b5cf6', '#10b981', '#ec4899', '#f59e0b', '#ffffff'];
        
        // Create particles
        for (let i = 0; i < 150; i++) {
            particles.push({
                x: canvas.width / 2,
                y: canvas.height / 2,
                vx: (Math.random() - 0.5) * 15,
                vy: Math.random() * -20 - 5,
                color: colors[Math.floor(Math.random() * colors.length)],
                size: Math.random() * 8 + 3,
                rotation: Math.random() * 360,
                rotationSpeed: (Math.random() - 0.5) * 15,
                gravity: 0.3,
                friction: 0.99,
                opacity: 1
            });
        }
        
        function animate() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            let stillVisible = false;
            
            particles.forEach(p => {
                p.vy += p.gravity;
                p.vx *= p.friction;
                p.x += p.vx;
                p.y += p.vy;
                p.rotation += p.rotationSpeed;
                
                if (p.y > canvas.height) {
                    p.opacity -= 0.02;
                }
                
                if (p.opacity > 0) {
                    stillVisible = true;
                    ctx.save();
                    ctx.globalAlpha = p.opacity;
                    ctx.translate(p.x, p.y);
                    ctx.rotate(p.rotation * Math.PI / 180);
                    ctx.fillStyle = p.color;
                    ctx.fillRect(-p.size/2, -p.size/2, p.size, p.size);
                    ctx.restore();
                }
            });
            
            if (stillVisible) {
                requestAnimationFrame(animate);
            } else {
                canvas.remove();
            }
        }
        
        animate();
    })();
    </script>
    '''
    
    return f'''
    {confetti_js}
    
    <style>
    /* Success celebration enhancements */
    .premium-success-container {{
        position: relative;
        overflow: hidden;
    }}
    
    .success-glow {{
        position: absolute;
        width: 200px;
        height: 200px;
        background: radial-gradient(circle, rgba(16, 185, 129, 0.3) 0%, transparent 70%);
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        animation: glowPulse 2s ease-in-out infinite;
        pointer-events: none;
    }}
    
    @keyframes glowPulse {{
        0%, 100% {{ transform: translate(-50%, -50%) scale(1); opacity: 0.5; }}
        50% {{ transform: translate(-50%, -50%) scale(1.2); opacity: 0.8; }}
    }}
    
    .success-title-animated {{
        animation: titleBounce 0.6s ease-out forwards;
    }}
    
    @keyframes titleBounce {{
        0% {{ transform: scale(0.5); opacity: 0; }}
        50% {{ transform: scale(1.1); }}
        100% {{ transform: scale(1); opacity: 1; }}
    }}
    
    .metric-pop {{
        animation: metricPop 0.5s ease-out forwards;
        opacity: 0;
    }}
    
    .metric-pop:nth-child(1) {{ animation-delay: 0.3s; }}
    .metric-pop:nth-child(2) {{ animation-delay: 0.4s; }}
    .metric-pop:nth-child(3) {{ animation-delay: 0.5s; }}
    .metric-pop:nth-child(4) {{ animation-delay: 0.6s; }}
    
    @keyframes metricPop {{
        0% {{ transform: scale(0) translateY(20px); opacity: 0; }}
        100% {{ transform: scale(1) translateY(0); opacity: 1; }}
    }}
    </style>
    
    <div class="premium-glass-panel premium-success premium-success-container">
        <div class="success-glow"></div>
        
        <div class="premium-success-icon">
            <svg viewBox="0 0 80 80">
                <circle class="premium-success-circle" cx="40" cy="40" r="38"/>
                <path class="premium-success-check" d="M24 42 L34 52 L56 28"/>
            </svg>
        </div>
        
        <div class="premium-success-title success-title-animated">🎉 Processing Complete!</div>
        <div class="premium-success-subtitle">
            {total_files} file(s) • {total_chunks} chunks • {elapsed:.1f}s
        </div>
        
        <div class="premium-metrics" style="margin-top: 24px;">
            <div class="premium-metric-card metric-pop">
                <div class="premium-metric-icon">✨</div>
                <div class="premium-metric-value" style="color: var(--accent-green);">{actions.get('INSERT', 0)}</div>
                <div class="premium-metric-label">New Chunks</div>
            </div>
            <div class="premium-metric-card metric-pop">
                <div class="premium-metric-icon">🔀</div>
                <div class="premium-metric-value" style="color: var(--accent-purple);">{actions.get('MERGE', 0)}</div>
                <div class="premium-metric-label">Merged</div>
            </div>
            <div class="premium-metric-card metric-pop">
                <div class="premium-metric-icon">🔄</div>
                <div class="premium-metric-value" style="color: var(--accent-cyan);">{actions.get('REPLACEMENT', 0)}</div>
                <div class="premium-metric-label">Replaced</div>
            </div>
            <div class="premium-metric-card metric-pop">
                <div class="premium-metric-icon">📊</div>
                <div class="premium-metric-value" style="color: var(--accent-yellow);">{total_chunks}</div>
                <div class="premium-metric-label">Total</div>
            </div>
        </div>
    </div>
    '''


def render_error_state(error_message: str) -> str:
    """Render an error state with shake animation."""
    
    return f'''
    <style>
    .error-shake {{
        animation: errorShake 0.6s ease-in-out;
    }}
    
    @keyframes errorShake {{
        0%, 100% {{ transform: translateX(0); }}
        10%, 30%, 50%, 70%, 90% {{ transform: translateX(-10px); }}
        20%, 40%, 60%, 80% {{ transform: translateX(10px); }}
    }}
    
    .error-icon-pulse {{
        animation: errorPulse 1.5s ease-in-out infinite;
    }}
    
    @keyframes errorPulse {{
        0%, 100% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }}
        50% {{ box-shadow: 0 0 0 20px rgba(239, 68, 68, 0); }}
    }}
    </style>
    
    <div class="premium-glass-panel error-shake" style="border-color: var(--accent-red);">
        <div style="text-align: center; padding: 20px;">
            <div class="error-icon-pulse" style="
                width: 64px;
                height: 64px;
                border-radius: 50%;
                background: rgba(239, 68, 68, 0.1);
                border: 2px solid var(--accent-red);
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 16px;
                font-size: 28px;
            ">❌</div>
            <div style="font-size: 18px; font-weight: 600; color: var(--accent-red); margin-bottom: 8px;">
                Processing Failed
            </div>
            <div style="font-size: 14px; color: var(--text-secondary);">
                {error_message}
            </div>
        </div>
    </div>
    '''


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'PREMIUM_CSS',
    'STAGE_ICONS',
    'STAGE_COLORS',
    'PREMIUM_STAGES',
    'render_premium_progress',
    'render_premium_success',
    'render_error_state'
]

