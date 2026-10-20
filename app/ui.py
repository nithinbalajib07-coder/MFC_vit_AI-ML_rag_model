"""
SMU Assistant - Grounded FAQ Knowledge Portal
Design System: Academic Precision & Institutional Heritage (Saint Mary's University)

A restrained, credible, university-branded knowledge portal with clear information hierarchy,
rich campus photography, common question shortcuts, verifiable citations,
and multi-tier retrieval diagnostics.
"""

import html
import math
import streamlit as st
import streamlit.components.v1 as components
from src.pipeline import RAGPipeline

st.set_page_config(
    page_title="SMU Assistant | Knowledge Services",
    page_icon="assets/bot_avatar.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

BOT_AVATAR = "assets/bot_avatar.png"
USER_AVATAR = "assets/user_avatar.png"

# ----------------------------------------------------------------------------
# Design System & Styling (Academic Precision & Institutional Portal)
# ----------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400&display=swap');

:root {
    /* Brand & Accent Tokens (Saint Mary's University) */
    --primary-burgundy: #8B123C;
    --burgundy-hover: #720E31;
    --burgundy-light: #FDF2F5;
    --burgundy-border: #F7D5DF;
    
    /* Deep Navy & Typography Tokens */
    --deep-navy: #163453;
    --navy-dark: #0F2338;
    --primary-text: #19324D;
    --secondary-text: #68788A;
    
    /* Surface & Background Tokens */
    --main-bg: #FAF9F6;
    --surface: #FFFFFF;
    --border: #D9DFE5;
    --border-light: #EAEFF4;
    --accent-bg: #F3F5F8;
    
    /* Semantic Status Tokens */
    --emerald-dark: #0F766E;
    --emerald-light: #F0FDF4;
    --emerald-border: #BBF7D0;
    
    --amber-dark: #92400E;
    --amber-light: #FFFBEB;
    --amber-border: #FDE68A;
    
    /* Radii */
    --radius-sm: 4px;
    --radius-md: 6px;
    --radius-lg: 8px;
}

/* Base resets & typography */
html {
    scroll-behavior: smooth;
}
html, body, [class*="css"], .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    color: var(--primary-text);
}
.stApp {
    background-color: var(--main-bg) !important;
}

/* Streamlit chrome adjustments: hide deploy & 3-dot menu, PRESERVE toolbar & expand button */
#MainMenu, 
footer, 
.stDeployButton, 
[data-testid="stAppDeployButton"], 
[data-testid="stDecoration"],
[data-testid="stToolbarActions"],
[data-testid="stStatusWidget"] {
    visibility: hidden !important;
    display: none !important;
    height: 0 !important;
    width: 0 !important;
}

header[data-testid="stHeader"] {
    background: transparent !important;
    height: 3.25rem !important;
    z-index: 1000 !important;
    pointer-events: none !important;
}

[data-testid="stToolbar"] {
    visibility: visible !important;
    display: flex !important;
    height: 3.25rem !important;
    background: transparent !important;
    pointer-events: none !important;
}

/* Ensure the native sidebar expand button is ALWAYS visible, prominent, and clickable when collapsed */
[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapsedControl"] {
    visibility: visible !important;
    display: inline-flex !important;
    opacity: 1 !important;
    pointer-events: auto !important;
    z-index: 999999 !important;
    position: fixed !important;
    top: 14px !important;
    left: 14px !important;
    background: #FFFFFF !important;
    color: var(--primary-burgundy) !important;
    border: 1.5px solid #8B123C !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 14px rgba(139, 18, 60, 0.18) !important;
    padding: 6px 10px !important;
    cursor: pointer !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

[data-testid="stExpandSidebarButton"]:hover,
[data-testid="stSidebarCollapsedControl"]:hover {
    background: #8B123C !important;
    color: #FFFFFF !important;
    box-shadow: 0 6px 18px rgba(139, 18, 60, 0.28) !important;
}

[data-testid="stExpandSidebarButton"] button,
[data-testid="stSidebarCollapsedControl"] button {
    color: inherit !important;
    background: transparent !important;
    border: none !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
}

[data-testid="stExpandSidebarButton"] svg,
[data-testid="stSidebarCollapsedControl"] svg {
    color: inherit !important;
    fill: currentColor !important;
    stroke: currentColor !important;
    width: 20px !important;
    height: 20px !important;
}

.block-container {
    padding-top: 2rem !important;
    padding-bottom: 6rem !important;
    max-width: 980px !important;
    margin: 0 auto !important;
}

/* Accessible focus ring */
button:focus-visible,
input:focus-visible,
[tabindex="0"]:focus-visible {
    outline: 2px solid var(--primary-burgundy) !important;
    outline-offset: 2px !important;
}

/* ---------- Sidebar Styling ---------- */
[data-testid="stSidebar"] {
    background-color: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"][aria-expanded="true"] {
    min-width: 320px !important;
    max-width: 360px !important;
}
[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem !important;
    padding-left: 1.25rem !important;
    padding-right: 1.25rem !important;
    max-width: 100% !important;
}

.smu-sidebar-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 6px;
    padding-top: 4px;
}
.smu-brand-crest {
    width: 36px;
    height: 36px;
    border-radius: var(--radius-md);
    background: var(--burgundy-light);
    border: 1px solid var(--burgundy-border);
    display: grid;
    place-items: center;
    flex-shrink: 0;
}
.smu-brand-name {
    font-family: 'Source Serif 4', Georgia, serif;
    font-weight: 700;
    font-size: 1.15rem;
    line-height: 1.15;
    color: var(--deep-navy);
}
.smu-brand-sub {
    font-size: 0.74rem;
    color: var(--secondary-text);
    font-weight: 500;
    letter-spacing: 0.02em;
}
.smu-sidebar-divider {
    border: none;
    height: 1px;
    background: var(--border);
    margin: 12px 0 16px 0;
}

.sidebar-section-title {
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    color: var(--secondary-text) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    margin: 20px 0 8px 0 !important;
}

/* Sidebar Radio Buttons */
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    font-size: 0.88rem !important;
    color: var(--primary-text) !important;
    font-weight: 500 !important;
    padding: 3px 0 !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] [data-checked="true"] {
    border-color: var(--primary-burgundy) !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] [data-checked="true"] > div {
    background-color: var(--primary-burgundy) !important;
}

/* Sidebar Toggle */
[data-testid="stSidebar"] [data-testid="stToggle"] {
    margin-top: 6px !important;
}
[data-testid="stSidebar"] [data-testid="stToggle"] label {
    font-size: 0.88rem !important;
    color: var(--primary-text) !important;
    font-weight: 500 !important;
}
[data-testid="stSidebar"] [data-testid="stToggle"] [aria-checked="true"] {
    background-color: var(--primary-burgundy) !important;
}

/* Sidebar Selectbox */
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
    background-color: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    font-size: 0.88rem !important;
    color: var(--primary-text) !important;
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div:focus-within {
    border-color: var(--primary-burgundy) !important;
    box-shadow: 0 0 0 2px rgba(139, 18, 60, 0.12) !important;
}

/* Cache Analytics Card */
.analytics-card {
    display: grid;
    grid-template-columns: 1fr 1fr;
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    background: var(--surface);
    overflow: hidden;
    margin: 8px 0 16px 0;
}
.analytics-cell {
    padding: 10px 8px;
    text-align: center;
    background: var(--surface);
    border-right: 1px solid var(--border-light);
    border-bottom: 1px solid var(--border-light);
}
.analytics-cell:nth-child(2), .analytics-cell:nth-child(4) {
    border-right: none;
}
.analytics-cell:nth-child(3), .analytics-cell:nth-child(4) {
    border-bottom: none;
}
.analytics-num {
    font-family: 'Inter', sans-serif;
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--deep-navy);
    line-height: 1.15;
}
.analytics-lbl {
    font-size: 0.65rem;
    font-weight: 600;
    color: var(--secondary-text);
    letter-spacing: 0.06em;
    margin-top: 2px;
}

/* Sidebar Clear Button */
[data-testid="stSidebar"] div.stButton > button {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    color: var(--primary-text) !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    height: 38px !important;
    min-height: 38px !important;
    padding: 0 14px !important;
    justify-content: center !important;
    text-align: center !important;
    box-shadow: 0 1px 2px rgba(22, 52, 83, 0.04) !important;
    transition: all 0.15s ease !important;
    margin-top: 8px !important;
}
[data-testid="stSidebar"] div.stButton > button:hover {
    background: var(--burgundy-light) !important;
    border-color: var(--primary-burgundy) !important;
    color: var(--primary-burgundy) !important;
    box-shadow: none !important;
    transform: none !important;
}

/* ---------- Editorial Main Header & Visual ---------- */
.portal-header {
    margin-bottom: 10px;
}
.portal-eyebrow {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.74rem;
    font-weight: 700;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: var(--secondary-text);
    margin-bottom: 10px;
}
.eyebrow-accent {
    width: 18px;
    height: 3px;
    background: var(--primary-burgundy);
    border-radius: 2px;
    display: inline-block;
}
.portal-title {
    font-family: 'Source Serif 4', Georgia, serif;
    font-size: 2.5rem;
    font-weight: 600;
    color: var(--deep-navy);
    line-height: 1.18;
    margin: 0 0 12px 0;
    letter-spacing: -0.01em;
}
.portal-subtitle {
    font-size: 1.02rem;
    color: var(--secondary-text);
    line-height: 1.55;
    margin: 0;
}


/* ---------- Campus Image Card Styling ---------- */
[data-testid="stImage"] img {
    border-radius: var(--radius-lg) !important;
    border: 1px solid var(--border) !important;
    box-shadow: 0 3px 12px rgba(22, 52, 83, 0.08) !important;
    object-fit: cover !important;
}
[data-testid="stImage"] [data-testid="stImageCaption"] {
    font-size: 0.75rem !important;
    color: var(--secondary-text) !important;
    font-style: italic !important;
    margin-top: 6px !important;
    text-align: center !important;
}

/* ---------- Section Divider Headings ---------- */
.section-divider-heading {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 28px 0 16px 0;
}
.section-divider-heading span {
    font-size: 0.76rem;
    font-weight: 700;
    color: var(--secondary-text);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    white-space: nowrap;
}
.section-divider-heading .divider-line {
    flex: 1;
    height: 1px;
    background: var(--border);
}

/* ---------- Common Questions 2-Column Grid ---------- */
.common-questions-section div.stButton > button {
    width: 100% !important;
    height: 56px !important;
    min-height: 56px !important;
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    padding: 0 20px 0 52px !important;
    color: var(--deep-navy) !important;
    font-size: 0.93rem !important;
    font-weight: 500 !important;
    text-align: left !important;
    justify-content: flex-start !important;
    box-shadow: 0 1px 2px rgba(22, 52, 83, 0.03) !important;
    transition: border-color 0.15s ease, background 0.15s ease, color 0.15s ease !important;
    background-repeat: no-repeat !important;
    background-position: 18px center !important;
    background-size: 19px 19px !important;
    position: relative !important;
    margin-bottom: 8px !important;
}
.common-questions-section div.stButton > button:hover {
    border-color: var(--primary-burgundy) !important;
    background-color: var(--main-bg) !important;
    color: var(--primary-burgundy) !important;
    box-shadow: 0 2px 5px rgba(139, 18, 60, 0.06) !important;
    transform: none !important;
}
.common-questions-section div.stButton > button::after {
    content: "›" !important;
    position: absolute !important;
    right: 18px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    font-size: 1.35rem !important;
    font-weight: 300 !important;
    color: #94A3B8 !important;
    line-height: 1 !important;
}
.common-questions-section div.stButton > button:hover::after {
    color: var(--primary-burgundy) !important;
}

/* Column 1 Line Icons (Ticket, ID Card, Credit Card) */
[data-testid="stColumn"]:has(.cq-col-left) div.stButton:nth-of-type(1) > button {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='%238B123C' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='2' y='6' width='20' height='12' rx='2'/%3E%3Cpath d='M10 6v12'/%3E%3Ccircle cx='6' cy='12' r='1.5'/%3E%3Ccircle cx='18' cy='12' r='1.5'/%3E%3C/svg%3E") !important;
}
[data-testid="stColumn"]:has(.cq-col-left) div.stButton:nth-of-type(2) > button {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='%238B123C' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='2' y='4' width='20' height='16' rx='2'/%3E%3Ccircle cx='8' cy='10' r='2'/%3E%3Cpath d='M14 10h4'/%3E%3Cpath d='M6 16c0-1.5 1.5-2.5 3-2.5s3 1 3 2.5'/%3E%3Cpath d='M14 14h4'/%3E%3C/svg%3E") !important;
}
[data-testid="stColumn"]:has(.cq-col-left) div.stButton:nth-of-type(3) > button {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='%238B123C' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='2' y='5' width='20' height='14' rx='2'/%3E%3Cline x1='2' y1='10' x2='22' y2='10'/%3E%3C/svg%3E") !important;
}

/* Column 2 Line Icons (Bus, Laptop, Dining) */
[data-testid="stColumn"]:has(.cq-col-right) div.stButton:nth-of-type(1) > button {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='%238B123C' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='3' width='18' height='15' rx='3'/%3E%3Cpath d='M3 9h18'/%3E%3Cpath d='M7 15h.01'/%3E%3Cpath d='M17 15h.01'/%3E%3Cpath d='M5 18v3'/%3E%3Cpath d='M19 18v3'/%3E%3C/svg%3E") !important;
}
[data-testid="stColumn"]:has(.cq-col-right) div.stButton:nth-of-type(2) > button {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='%238B123C' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='4' width='18' height='12' rx='2'/%3E%3Cpath d='M2 20h20'/%3E%3Cline x1='12' y1='16' x2='12' y2='20'/%3E%3C/svg%3E") !important;
}
[data-testid="stColumn"]:has(.cq-col-right) div.stButton:nth-of-type(3) > button {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='%238B123C' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M18 2v20'/%3E%3Cpath d='M21 15V2a5 5 0 0 0-5 5v8h5zm0 0v7'/%3E%3Cpath d='M4 2v7a3 3 0 0 0 3 3v10'/%3E%3Cpath d='M10 2v7a3 3 0 0 1-3 3'/%3E%3Cpath d='M7 2v10'/%3E%3C/svg%3E") !important;
}

/* ---------- Welcome Panel ---------- */
.welcome-panel {
    display: flex;
    flex-direction: column;
    gap: 8px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 20px 22px;
    box-shadow: 0 1px 4px rgba(22, 52, 83, 0.03);
    height: 100%;
}
.welcome-header-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 6px;
}
.welcome-icon {
    flex-shrink: 0;
    width: 34px;
    height: 34px;
    border-radius: var(--radius-md);
    background: var(--burgundy-light);
    border: 1px solid var(--burgundy-border);
    display: grid;
    place-items: center;
}
.welcome-title {
    font-family: 'Source Serif 4', Georgia, serif;
    font-size: 1.12rem;
    font-weight: 700;
    color: var(--deep-navy);
}
.welcome-text {
    font-size: 0.94rem;
    line-height: 1.62;
    color: var(--primary-text);
    margin: 0;
}
.welcome-hint {
    font-size: 0.88rem;
    color: var(--secondary-text);
    margin: 6px 0 0 0;
    line-height: 1.5;
}
.welcome-subnote {
    font-size: 0.78rem;
    color: var(--secondary-text);
    font-style: italic;
    margin-top: 8px;
}

/* ---------- Chat Messages ---------- */
[data-testid="stChatMessage"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    padding: 18px 22px !important;
    margin-bottom: 16px !important;
    box-shadow: 0 1px 3px rgba(22, 52, 83, 0.03) !important;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    background: var(--accent-bg) !important;
    border-color: var(--border) !important;
}
[data-testid="stChatMessageAvatar"] {
    width: 32px !important;
    height: 32px !important;
    border-radius: var(--radius-sm) !important;
    background: var(--main-bg) !important;
    border: 1px solid var(--border) !important;
}
[data-testid="stChatMessage"] p {
    font-size: 0.96rem !important;
    line-height: 1.65 !important;
    color: var(--primary-text) !important;
}

/* ---------- Trust & Verification Strip (Meta) ---------- */
.trust-strip {
    margin-top: 16px;
    padding-top: 14px;
    border-top: 1px solid var(--border-light);
}
.trust-primary-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 10px;
}
.trust-badges {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
}
.trust-chip {
    font-family: 'Inter', sans-serif;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: var(--radius-sm);
    display: inline-flex;
    align-items: center;
    gap: 6px;
    line-height: 1;
}
.trust-chip.grounded {
    background: var(--emerald-light);
    color: var(--emerald-dark);
    border: 1px solid var(--emerald-border);
}
.trust-chip.unverified {
    background: var(--amber-light);
    color: var(--amber-dark);
    border: 1px solid var(--amber-border);
}
.trust-chip.cached {
    background: var(--accent-bg);
    color: var(--deep-navy);
    border: 1px solid var(--border);
}
.trust-chip.neutral {
    background: var(--surface);
    color: var(--secondary-text);
    border: 1px solid var(--border);
}

/* Confidence meter block */
.confidence-box {
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 170px;
}
.confidence-label {
    font-size: 0.73rem;
    font-weight: 600;
    color: var(--secondary-text);
    white-space: nowrap;
}
.confidence-meter {
    flex: 1;
    height: 6px;
    background: var(--border-light);
    border-radius: 3px;
    overflow: hidden;
    position: relative;
    border: 1px solid var(--border);
}
.confidence-meter > span {
    display: block;
    height: 100%;
    border-radius: 3px;
    transition: width 0.7s cubic-bezier(0.16, 1, 0.3, 1);
}

/* Diagnostics cluster */
.diagnostics-cluster {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    align-items: center;
}
.diag-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    font-weight: 500;
    padding: 3px 8px;
    border-radius: var(--radius-sm);
    background: var(--accent-bg);
    color: var(--secondary-text);
    border: 1px solid var(--border);
}

/* ---------- Source Citations Expander & Cards ---------- */
[data-testid="stExpander"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    background: var(--main-bg) !important;
    box-shadow: none !important;
    margin-top: 14px !important;
}
[data-testid="stExpander"] summary {
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    color: var(--deep-navy) !important;
    padding: 8px 12px !important;
}
[data-testid="stExpander"] summary:hover {
    color: var(--primary-burgundy) !important;
}
[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    background: var(--surface) !important;
    border-top: 1px solid var(--border-light) !important;
    padding: 12px 16px !important;
}

.source-card {
    background: #FFFFFF;
    border: 1px solid var(--border);
    border-left: 3px solid var(--primary-burgundy);
    border-radius: var(--radius-sm);
    padding: 12px 16px;
    margin: 10px 0;
    box-shadow: 0 1px 2px rgba(22, 52, 83, 0.02);
}
.source-card:hover {
    border-color: #CBD5E1;
    border-left-color: var(--primary-burgundy);
    box-shadow: 0 2px 6px rgba(22, 52, 83, 0.04);
}
.source-header {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 6px;
}
.source-id-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    font-weight: 700;
    color: var(--primary-burgundy);
    background: var(--burgundy-light);
    border: 1px solid var(--burgundy-border);
    padding: 2px 7px;
    border-radius: var(--radius-sm);
    letter-spacing: 0.03em;
}
.source-cat-chip {
    font-size: 0.70rem;
    font-weight: 500;
    color: var(--secondary-text);
    background: var(--accent-bg);
    border: 1px solid var(--border);
    padding: 2px 8px;
    border-radius: 12px;
}
.source-score-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.70rem;
    font-weight: 600;
    color: var(--deep-navy);
}
.source-question {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    font-size: 0.88rem;
    color: var(--deep-navy);
    margin: 4px 0 6px 0;
    line-height: 1.35;
}
.source-snippet {
    font-size: 0.84rem;
    color: var(--primary-text);
    line-height: 1.55;
    background: var(--main-bg);
    padding: 8px 12px;
    border-radius: var(--radius-sm);
    border-left: 2px solid var(--border);
}
.source-meter-bar {
    height: 3px;
    background: var(--border-light);
    border-radius: 2px;
    margin-top: 8px;
    overflow: hidden;
}
.source-meter-bar > span {
    display: block;
    height: 100%;
    background: var(--primary-burgundy);
    border-radius: 2px;
}

/* ---------- Bottom Chat Input ---------- */
[data-testid="stChatInput"] {
    border-radius: var(--radius-md) !important;
    border: 1.5px solid var(--border) !important;
    background: var(--surface) !important;
    box-shadow: 0 2px 8px rgba(22, 52, 83, 0.05) !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: var(--primary-burgundy) !important;
    box-shadow: 0 0 0 3px rgba(139, 18, 60, 0.12) !important;
}
[data-testid="stChatInput"] textarea {
    font-size: 0.95rem !important;
    color: var(--primary-text) !important;
}
[data-testid="stChatInput"] button {
    color: var(--primary-burgundy) !important;
}

/* ---------- Form & Search Input ---------- */
[data-testid="stForm"] {
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    background: var(--surface) !important;
    padding: 8px 12px !important;
    box-shadow: 0 2px 6px rgba(22, 52, 83, 0.04) !important;
    margin-top: 14px !important;
}
[data-testid="stForm"]:focus-within {
    border-color: var(--primary-burgundy) !important;
    box-shadow: 0 0 0 3px rgba(139, 18, 60, 0.12) !important;
}
[data-testid="stForm"] div.stButton > button {
    background-color: var(--primary-burgundy) !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
    border-radius: var(--radius-sm) !important;
    border: none !important;
    height: 42px !important;
}
[data-testid="stForm"] div.stButton > button:hover {
    background-color: var(--burgundy-hover) !important;
}

/* Responsive Breakpoints */
@media (max-width: 768px) {
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    .portal-title {
        font-size: 1.95rem !important;
    }
    .portal-subtitle {
        font-size: 0.95rem !important;
    }
    .common-questions-section div.stButton > button {
        height: auto !important;
        min-height: 52px !important;
        padding: 12px 16px 12px 46px !important;
    }
    .trust-primary-row {
        flex-direction: column !important;
        align-items: flex-start !important;
    }
    .confidence-box {
        width: 100% !important;
    }
}

/* ============================================================================
   MINIMAL LOADING INDICATOR (Pure Text & Spinning Icon - No Effects)
   ============================================================================ */
@keyframes smuSpin {
    from {
        transform: rotate(0deg);
    }
    to {
        transform: rotate(360deg);
    }
}

/* Base Spinner Elements (Global) - Simple inline/row layout, zero card borders/shadows */
.stSpinner, [data-testid="stSpinner"] {
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 8px !important;
    margin: 8px auto !important;
}

.stSpinner > div,
.stCacheSpinner > div,
[data-testid="stSpinner"] > div {
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    gap: 10px !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    width: auto !important;
}

/* Cache Resource Initial Load - Centered, purely text and spinning icon */
.stCacheSpinner {
    position: fixed !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) !important;
    z-index: 99999 !important;
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    justify-content: center !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
    width: auto !important;
}

/* Completely remove backdrop scrim */
.stCacheSpinner::before {
    display: none !important;
    content: none !important;
}

/* Spinner SVG Icon - Standard rotating circle */
.stSpinner svg,
.stCacheSpinner svg,
[data-testid="stSpinner"] svg {
    width: 26px !important;
    height: 26px !important;
    color: #8B123C !important;
    animation: smuSpin 0.85s linear infinite !important;
    filter: none !important;
}

.stSpinner svg circle,
.stCacheSpinner svg circle,
[data-testid="stSpinner"] svg circle {
    stroke: #8B123C !important;
    stroke-width: 3px !important;
}

/* Loading Typography - Clean, readable standard font, no shimmer/effects */
.stSpinner span,
.stCacheSpinner span,
[data-testid="stSpinner"] span,
.stSpinner p,
.stCacheSpinner p,
[data-testid="stSpinner"] p {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    font-size: 1rem !important;
    font-weight: 500 !important;
    color: #163453 !important;
    -webkit-text-fill-color: #163453 !important;
    background: none !important;
    text-align: left !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* Elapsed Time Subtext */
.stSpinner span:last-child[class*="seconds"],
.stCacheSpinner span:last-child[class*="seconds"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.82rem !important;
    font-weight: 400 !important;
    color: var(--secondary-text) !important;
    -webkit-text-fill-color: var(--secondary-text) !important;
    background: none !important;
    margin-left: 6px !important;
}

/* Remove all card badges and pseudo-element text */
.stCacheSpinner > div::after,
.stSpinner > div::after,
[data-testid="stSpinner"] > div::after {
    display: none !important;
    content: none !important;
}
</style>
""",
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------------
# Core Helper Functions
# ----------------------------------------------------------------------------
@st.cache_resource(show_spinner="Loading SMU knowledge engine and indexes...")
def get_pipeline():
    return RAGPipeline()


def clamp01(x: float) -> float:
    try:
        return max(0.0, min(1.0, float(x)))
    except (TypeError, ValueError):
        return 0.0


def score_to_pct(score) -> int:
    """Map any relevance score (RRF, cosine, or cross-encoder logit) to 0-100 for display."""
    try:
        s = float(score)
    except (TypeError, ValueError):
        return 0
    if 0.0 <= s <= 1.0:
        return int(s * 100)
    return int(100 / (1 + math.exp(-s / 2.0)))


def meta_html(result: dict) -> str:
    """Render an accessible, WCAG-compliant Trust & Verification strip below assistant answers."""
    conf = clamp01(result.get("confidence", 0.0))
    conf_pct = int(conf * 100)

    if conf >= 0.6:
        bar_color = "#0F766E"  # emerald
        conf_label = "High Confidence"
    elif conf >= 0.35:
        bar_color = "#D97706"  # amber
        conf_label = "Moderate"
    else:
        bar_color = "#DC2626"  # red
        conf_label = "Low Confidence"

    svg_cache = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-1px; margin-right:4px;"><polyline points="20 6 9 17 4 12"></polyline></svg>'
    svg_clock = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-1px; margin-right:4px;"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>'
    svg_check = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-1px; margin-right:4px;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>'
    svg_shield_alert = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-1px; margin-right:4px;"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>'

    if result.get("cached"):
        hit_type = html.escape(str(result.get("cache_hit_type", "exact")))
        speed_badge = f"<span class='trust-chip cached'>{svg_cache}Cache Hit · {hit_type}</span>"
    else:
        lat = result.get("latency_ms", 0)
        speed_badge = f"<span class='trust-chip neutral'>{svg_clock}{lat} ms</span>"

    if result.get("is_grounded"):
        grounded_badge = f"<span class='trust-chip grounded'>{svg_check}Grounded in Sources</span>"
    else:
        grounded_badge = f"<span class='trust-chip unverified'>{svg_shield_alert}Not Grounded · Abstained</span>"

    backend = html.escape(str(result.get("backend", "Gemini 2.5 Flash")))
    mode = html.escape(str(result.get("mode", "hybrid_rrf")))

    return f"""
<div class="trust-strip">
    <div class="trust-primary-row">
        <div class="trust-badges">
            {grounded_badge}
            {speed_badge}
        </div>
        <div class="confidence-box" title="Retrieval and generation confidence score">
            <span class="confidence-label">Confidence: {conf_pct}% ({conf_label})</span>
            <div class="confidence-meter" role="progressbar" aria-valuenow="{conf_pct}" aria-valuemin="0" aria-valuemax="100" aria-label="Answer confidence score">
                <span style="width:{conf_pct}%;background:{bar_color};"></span>
            </div>
        </div>
    </div>
    <div class="diagnostics-cluster">
        <span class="diag-tag">Model: {backend}</span>
        <span class="diag-tag">Strategy: {mode}</span>
    </div>
</div>
"""


def sources_html(sources: list) -> str:
    """Format supporting FAQ passages as structured academic index cards."""
    cards = []
    for s in sources:
        pct = score_to_pct(s.get("score", 0))
        faq_id = html.escape(str(s.get("faq_id", "SMU-FAQ")))
        q_text = html.escape(str(s.get("question", "")))
        snippet = html.escape(str(s.get("snippet", "")))
        category = html.escape(str(s.get("category", "General")))

        cards.append(
            f"""
<div class="source-card">
    <div class="source-header">
        <span class="source-id-badge">{faq_id}</span>
        <span class="source-cat-chip">{category}</span>
        <span class="source-score-badge">Match: {pct}%</span>
    </div>
    <div class="source-question">{q_text}</div>
    <div class="source-snippet">"{snippet}"</div>
    <div class="source-meter-bar" role="progressbar" aria-valuenow="{pct}" aria-valuemin="0" aria-valuemax="100" aria-label="Passage relevance match">
        <span style="width:{pct}%;"></span>
    </div>
</div>
"""
        )
    return "".join(cards)


def render_message(msg: dict, expand_sources: bool = False):
    """Render chat markdown, metadata verification strip, and supporting source accordion."""
    st.markdown(msg["content"])
    if msg.get("meta"):
        st.markdown(msg["meta"], unsafe_allow_html=True)
    if msg.get("sources"):
        with st.expander(f"Supporting Sources ({len(msg['sources'])})", expanded=expand_sources):
            st.markdown(sources_html(msg["sources"]), unsafe_allow_html=True)


def trigger_auto_scroll():
    """Scroll smoothly down to the latest query and response using components.html."""
    components.html(
        """
        <script>
        (function() {
            function performScroll() {
                try {
                    const doc = window.parent.document;
                    const queryAnchor = doc.getElementById('active-user-query') || doc.getElementById('latest-response-anchor');
                    if (queryAnchor) {
                        queryAnchor.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        return;
                    }
                    const chatMsgs = doc.querySelectorAll('[data-testid="stChatMessage"]');
                    if (chatMsgs && chatMsgs.length > 0) {
                        chatMsgs[chatMsgs.length - 1].scrollIntoView({ behavior: 'smooth', block: 'start' });
                        return;
                    }
                    const scroller = doc.querySelector('[data-testid="stAppViewContainer"]') || 
                                     doc.querySelector('[data-testid="stMain"]') || 
                                     doc.querySelector('section.main') || 
                                     window.parent;
                    if (scroller && scroller.scrollTo) {
                        scroller.scrollTo({ top: scroller.scrollHeight || 999999, behavior: 'smooth' });
                    }
                } catch (e) {}
            }
            performScroll();
            setTimeout(performScroll, 60);
            setTimeout(performScroll, 200);
            setTimeout(performScroll, 450);
        })();
        </script>
        """,
        height=0,
        width=0,
    )



pipeline = get_pipeline()

# ----------------------------------------------------------------------------
# Floating & Accessible Sidebar Restore Button
# ----------------------------------------------------------------------------
sidebar_restore_button_js = """
<script>
(function() {
    function triggerSidebarOpen() {
        try {
            const doc = window.parent.document;
            const btn = doc.querySelector('[data-testid="stExpandSidebarButton"]') || 
                        doc.querySelector('[data-testid="stExpandSidebarButton"] button') ||
                        doc.querySelector('button[aria-label="Expand sidebar"]') ||
                        doc.querySelector('[data-testid="stSidebarCollapsedControl"] button') ||
                        doc.querySelector('[data-testid="stSidebarCollapsedControl"]');
            if (btn) {
                btn.click();
                btn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window.parent }));
                return true;
            }
        } catch(e) {}
        return false;
    }

    function initFloatingRestoreButton() {
        try {
            const doc = window.parent.document;
            if (!doc) return;

            let restoreBtn = doc.getElementById('smu-sidebar-restore-button');
            if (!restoreBtn) {
                restoreBtn = doc.createElement('button');
                restoreBtn.id = 'smu-sidebar-restore-button';
                restoreBtn.setAttribute('type', 'button');
                restoreBtn.setAttribute('aria-label', 'Open left side panel (Search modes & Cache analytics)');
                restoreBtn.title = 'Open Left Side Panel (Cache Analytics & Search Modes)';
                restoreBtn.innerHTML = `
                    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;">
                        <line x1="3" y1="12" x2="21" y2="12"></line>
                        <line x1="3" y1="6" x2="21" y2="6"></line>
                        <line x1="3" y1="18" x2="21" y2="18"></line>
                    </svg>
                    <span>Side Panel</span>
                `;

                restoreBtn.style.cssText = `
                    position: fixed !important;
                    top: 14px !important;
                    left: 14px !important;
                    z-index: 9999999 !important;
                    display: none;
                    align-items: center !important;
                    justify-content: center !important;
                    gap: 8px !important;
                    background: #FFFFFF !important;
                    color: #8B123C !important;
                    border: 1.5px solid #8B123C !important;
                    border-radius: 8px !important;
                    padding: 8px 14px !important;
                    font-family: 'Inter', -apple-system, sans-serif !important;
                    font-size: 0.82rem !important;
                    font-weight: 600 !important;
                    letter-spacing: 0.02em !important;
                    box-shadow: 0 4px 16px rgba(139, 18, 60, 0.2) !important;
                    cursor: pointer !important;
                    user-select: none !important;
                    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
                `;

                restoreBtn.addEventListener('mouseenter', function() {
                    restoreBtn.style.background = '#8B123C';
                    restoreBtn.style.color = '#FFFFFF';
                    restoreBtn.style.boxShadow = '0 6px 20px rgba(139, 18, 60, 0.32)';
                    restoreBtn.style.transform = 'translateY(-1px)';
                });

                restoreBtn.addEventListener('mouseleave', function() {
                    restoreBtn.style.background = '#FFFFFF';
                    restoreBtn.style.color = '#8B123C';
                    restoreBtn.style.boxShadow = '0 4px 16px rgba(139, 18, 60, 0.2)';
                    restoreBtn.style.transform = 'none';
                });

                restoreBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    triggerSidebarOpen();
                });

                doc.body.appendChild(restoreBtn);
            }

            function updateVisibility() {
                try {
                    const doc = window.parent.document;
                    const sidebar = doc.querySelector('section[data-testid="stSidebar"]') || doc.querySelector('[data-testid="stSidebar"]');
                    const isCollapsed = !sidebar || 
                                        sidebar.getAttribute('aria-expanded') === 'false' || 
                                        sidebar.getAttribute('data-collapsed') === 'true' ||
                                        sidebar.offsetWidth < 50;

                    if (restoreBtn) {
                        if (isCollapsed) {
                            restoreBtn.style.display = 'inline-flex';
                        } else {
                            restoreBtn.style.display = 'none';
                        }
                    }
                } catch(e) {}
            }

            updateVisibility();
            if (!window._smuSidebarWatcherActive) {
                window._smuSidebarWatcherActive = true;
                setInterval(updateVisibility, 150);
            }
        } catch(e) {}
    }

    initFloatingRestoreButton();
    setTimeout(initFloatingRestoreButton, 100);
    setTimeout(initFloatingRestoreButton, 500);
})();
</script>
"""
components.html(sidebar_restore_button_js, height=0, width=0)

# ----------------------------------------------------------------------------
# Sidebar Control & Analytics Center
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
<div class="smu-sidebar-brand">
    <div class="smu-brand-crest">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#8B123C" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2L3 7v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z"/>
            <path d="M12 22V12"/>
            <path d="M12 12l5-3"/>
            <path d="M12 12L7 9"/>
        </svg>
    </div>
    <div>
        <div class="smu-brand-name">SMU Assistant</div>
        <div class="smu-brand-sub">Knowledge Services</div>
    </div>
</div>
<hr class="smu-sidebar-divider" />
""",
        unsafe_allow_html=True,
    )

    st.markdown("<div class='sidebar-section-title'>RETRIEVAL</div>", unsafe_allow_html=True)
    retrieval_mode = st.radio(
        "Strategy",
        options=["hybrid_rrf", "dense_only", "sparse_only"],
        format_func=lambda x: {
            "hybrid_rrf": "Hybrid (Dense + BM25)",
            "dense_only": "Dense Semantic",
            "sparse_only": "BM25 Keyword",
        }[x],
        label_visibility="collapsed",
    )
    use_reranker = st.toggle("Cross-Encoder Reranking", value=True)
    pipeline.use_reranker = use_reranker

    st.markdown("<div class='sidebar-section-title'>SYNTHESIS ENGINE</div>", unsafe_allow_html=True)
    engine_choice = st.radio(
        "Generator Engine",
        options=["local_synthesizer", "gemini"],
        format_func=lambda x: {
            "local_synthesizer": "High-Speed Grounded (Instant ~0.3s)",
            "gemini": "Google Gemini API (Cloud LLM)",
        }[x],
        index=0,
        label_visibility="collapsed",
    )
    pipeline.generator.active_backend = engine_choice

    st.markdown("<div class='sidebar-section-title'>KNOWLEDGE SCOPE</div>", unsafe_allow_html=True)
    category_filter = st.selectbox(
        "Domain filter",
        [
            "All Domains",
            "Academics & Registration",
            "Tuition & Finance",
            "Campus & Transportation",
            "IT & Technical Support",
            "Athletics & Student Life",
            "Housing & Dining",
        ],
        label_visibility="collapsed",
    )
    active_category = None if category_filter == "All Domains" else category_filter

    st.markdown("<div class='sidebar-section-title'>CACHE ANALYTICS</div>", unsafe_allow_html=True)
    stats_slot = st.empty()

    if st.button("🗑 Clear Chat & Cache", use_container_width=True):
        pipeline.cache.exact_cache.clear()
        pipeline.cache.semantic_cache.clear()
        pipeline.cache.hits = 0
        pipeline.cache.misses = 0
        pipeline.cache.total_time_saved_ms = 0.0
        st.session_state.messages = []
        st.rerun()


def draw_stats():
    cs = pipeline.cache.get_stats()
    stats_slot.markdown(
        f"""
<div class="analytics-card">
    <div class="analytics-cell">
        <div class="analytics-num">{cs['hits']}</div>
        <div class="analytics-lbl">HITS</div>
    </div>
    <div class="analytics-cell">
        <div class="analytics-num">{cs['hit_rate_pct']}%</div>
        <div class="analytics-lbl">HIT RATE</div>
    </div>
    <div class="analytics-cell">
        <div class="analytics-num">{cs['cached_entries']}</div>
        <div class="analytics-lbl">ENTRIES</div>
    </div>
    <div class="analytics-cell">
        <div class="analytics-num">{cs['est_time_saved_sec']}s</div>
        <div class="analytics-lbl">SAVED</div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


draw_stats()

# ----------------------------------------------------------------------------
# Editorial Brand Header & Campus Hero Visual
# ----------------------------------------------------------------------------
hero_col_text, hero_col_img = st.columns([1.18, 0.82], gap="large")

with hero_col_text:
    st.markdown(
        """
<div class="portal-header">
    <div class="portal-eyebrow">
        <span class="eyebrow-accent"></span>
        <span>SAINT MARY'S UNIVERSITY / KNOWLEDGE BASE</span>
    </div>
    <h1 class="portal-title">What can we help you find?</h1>
    <p class="portal-subtitle">
        Accurate, grounded answers synthesized strictly from verified SMU documentation.
        Explore campus services, transit passes, course enrollment, tuition, and student life.
    </p>
</div>
""",
        unsafe_allow_html=True,
    )

@st.cache_data
def get_cached_image(path: str):
    with open(path, "rb") as f:
        return f.read()

with hero_col_img:
    st.image(
        get_cached_image("assets/smu_campus_hero.webp"),
        caption="Saint Mary's University Campus · Halifax, Nova Scotia",
        use_container_width=True,
    )

# ----------------------------------------------------------------------------
# Common Questions (Structured 2-Column Institutional Grid)
# ----------------------------------------------------------------------------
st.markdown(
    """
<div class="section-divider-heading">
    <span>COMMON QUESTIONS</span>
    <div class="divider-line"></div>
</div>
""",
    unsafe_allow_html=True,
)

common_questions = [
    {
        "title": "Tickets for home games",
        "query": "Where can I get tickets to SMU home games?",
    },
    {
        "title": "Metro Transit pass",
        "query": "Where do I get a pass for Metro Transit?",
    },
    {
        "title": "A-number and self-service banner",
        "query": "What is an A-Number and Self-Service Banner?",
    },
    {
        "title": "Computer and Wi-Fi support",
        "query": "Where do I go if I have computer problems?",
    },
    {
        "title": "Tuition and student fees",
        "query": "How do I make a tuition payment online?",
    },
    {
        "title": "Dining and campus hours",
        "query": "Where is the cafeteria located?",
    },
]

if "pending" not in st.session_state:
    st.session_state.pending = None

st.markdown('<div class="common-questions-section">', unsafe_allow_html=True)
col_left, col_right = st.columns(2)

with col_left:
    st.markdown('<div class="cq-col cq-col-left"></div>', unsafe_allow_html=True)
    for i in [0, 2, 4]:
        item = common_questions[i]
        if st.button(
            item["title"],
            key=f"cq_{i}",
            help=f"Query: {item['query']}",
            use_container_width=True,
        ):
            st.session_state.pending = item["query"]
            st.rerun()

with col_right:
    st.markdown('<div class="cq-col cq-col-right"></div>', unsafe_allow_html=True)
    for i in [1, 3, 5]:
        item = common_questions[i]
        if st.button(
            item["title"],
            key=f"cq_{i}",
            help=f"Query: {item['query']}",
            use_container_width=True,
        ):
            st.session_state.pending = item["query"]
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Recent Answers / Conversation Area
# ----------------------------------------------------------------------------
st.markdown(
    """
<div class="section-divider-heading">
    <span>RECENT ANSWERS</span>
    <div class="divider-line"></div>
</div>
""",
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    welcome_col_text, welcome_col_img = st.columns([1.18, 0.82], gap="large")
    with welcome_col_text:
        st.markdown(
            """
<div class="welcome-panel">
    <div class="welcome-header-row">
        <div class="welcome-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#8B123C" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                <line x1="9" y1="7" x2="15" y2="7"/>
                <line x1="9" y1="11" x2="13" y2="11"/>
            </svg>
        </div>
        <div class="welcome-title">SMU Knowledge Services</div>
    </div>
    <p class="welcome-text">
        Welcome! Ask anything regarding campus services, course registration, tuition deadlines,
        Metro Transit passes, IT support, student A-numbers, or campus dining.
    </p>
    <p class="welcome-hint">
        Select any common question above to begin, or type your own question in the input bar below.
    </p>
    <span class="welcome-subnote">Verifiable citations and confidence scores accompany every answer.</span>
</div>
""",
            unsafe_allow_html=True,
        )
    with welcome_col_img:
        st.image(
            get_cached_image("assets/smu_library_commons.webp"),
            caption="Patrick Power Library & Study Commons",
            use_container_width=True,
        )

for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar=BOT_AVATAR if m["role"] == "assistant" else USER_AVATAR):
        render_message(m)

# ----------------------------------------------------------------------------
# Bottom Query Composer & Execution Flow
# ----------------------------------------------------------------------------
typed = st.chat_input("Ask a question about Saint Mary's University...")

query = None
if st.session_state.pending:
    query = st.session_state.pending
    st.session_state.pending = None
elif typed and typed.strip():
    query = typed.strip()

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown("<div id='active-user-query' style='scroll-margin-top: 85px;'></div>", unsafe_allow_html=True)
        st.markdown(query)

    trigger_auto_scroll()

    with st.chat_message("assistant", avatar=BOT_AVATAR):
        with st.spinner("Synthesizing verified SMU documentation..."):
            result = pipeline.query(
                query, top_k=3, retrieval_mode=retrieval_mode, category_filter=active_category
            )
        reply = {
            "role": "assistant",
            "content": result["answer"],
            "meta": meta_html(result),
            "sources": result.get("sources", []),
        }
        st.markdown("<div id='latest-response-anchor' style='scroll-margin-top: 85px;'></div>", unsafe_allow_html=True)
        render_message(reply, expand_sources=True)

    st.session_state.messages.append(reply)
    draw_stats()
    trigger_auto_scroll()
