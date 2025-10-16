"""
Streamlit dashboard for monitoring the inquiry automation pipeline.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import time
from sqlalchemy import create_engine, text

# Page configuration
st.set_page_config(
    page_title="Inquiry Automation Pipeline Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database connection
@st.cache_resource
def get_db_connection():
    """Create database connection."""
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@postgres:5432/inquiry_automation"
    )
    engine = create_engine(db_url)
    return engine

# Data loading functions
@st.cache_data(ttl=10)
def load_inquiries(limit=1000):
    """Load recent inquiries."""
    engine = get_db_connection()
    query = text("""
        SELECT 
            i.id, i.subject, i.body, i.sender_email, i.timestamp, i.processed,
            p.category, p.sentiment, p.urgency,
            p.category_confidence, p.sentiment_confidence, p.urgency_confidence,
            r.department, r.assigned_consultant, r.priority_score, r.escalated
        FROM inquiries i
        LEFT JOIN predictions p ON i.id = p.inquiry_id
        LEFT JOIN routing_decisions r ON i.id = r.inquiry_id
        ORDER BY i.timestamp DESC
        LIMIT :limit
    """)
    
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"limit": limit})
    
    return df

@st.cache_data(ttl=10)
def load_statistics():
    """Load aggregated statistics."""
    engine = get_db_connection()
    
    with engine.connect() as conn:
        # Total counts
        total_inquiries = conn.execute(text("SELECT COUNT(*) FROM inquiries")).scalar()
        processed_inquiries = conn.execute(
            text("SELECT COUNT(*) FROM inquiries WHERE processed = TRUE")
        ).scalar()
        escalated_count = conn.execute(
            text("SELECT COUNT(*) FROM routing_decisions WHERE escalated = TRUE")
        ).scalar()
        
        # Category distribution
        category_dist = pd.read_sql(
            text("SELECT category, COUNT(*) as count FROM predictions GROUP BY category"),
            conn
        )
        
        # Department distribution
        dept_dist = pd.read_sql(
            text("SELECT department, COUNT(*) as count FROM routing_decisions GROUP BY department"),
            conn
        )
        
        # Urgency distribution
        urgency_dist = pd.read_sql(
            text("SELECT urgency, COUNT(*) as count FROM predictions GROUP BY urgency"),
            conn
        )
        
        # Sentiment distribution
        sentiment_dist = pd.read_sql(
            text("SELECT sentiment, COUNT(*) as count FROM predictions GROUP BY sentiment"),
            conn
        )
    
    return {
        'total': total_inquiries,
        'processed': processed_inquiries,
        'escalated': escalated_count,
        'category_dist': category_dist,
        'dept_dist': dept_dist,
        'urgency_dist': urgency_dist,
        'sentiment_dist': sentiment_dist,
    }

# Dashboard Header
st.title("📊 Inquiry Automation Pipeline Dashboard")
st.markdown("Real-time monitoring of client inquiry classification and routing")

# Sidebar filters
st.sidebar.header("Filters")
time_range = st.sidebar.selectbox(
    "Time Range",
    ["Last Hour", "Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"],
    index=2
)

category_filter = st.sidebar.multiselect(
    "Category",
    ["technical_support", "billing", "sales", "hr", "legal", "product_feedback"],
    default=[]
)

urgency_filter = st.sidebar.multiselect(
    "Urgency",
    ["low", "medium", "high", "critical"],
    default=[]
)

# Load data
try:
    df = load_inquiries()
    stats = load_statistics()
    
    # Apply filters
    if category_filter:
        df = df[df['category'].isin(category_filter)]
    if urgency_filter:
        df = df[df['urgency'].isin(urgency_filter)]
    
    # Key Metrics Row
    st.header("📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Inquiries",
            f"{stats['total']:,}",
            delta=None
        )
    
    with col2:
        processing_rate = (stats['processed'] / stats['total'] * 100) if stats['total'] > 0 else 0
        st.metric(
            "Processed",
            f"{stats['processed']:,}",
            delta=f"{processing_rate:.1f}%"
        )
    
    with col3:
        escalation_rate = (stats['escalated'] / stats['total'] * 100) if stats['total'] > 0 else 0
        st.metric(
            "Escalated",
            f"{stats['escalated']:,}",
            delta=f"{escalation_rate:.1f}%",
            delta_color="inverse"
        )
    
    with col4:
        avg_priority = df['priority_score'].mean() if len(df) > 0 else 0
        st.metric(
            "Avg Priority Score",
            f"{avg_priority:.1f}",
            delta=None
        )
    
    # Charts Row 1
    st.header("📊 Distributions")
    col1, col2 = st.columns(2)
    
    with col1:
        # Category Distribution
        if not stats['category_dist'].empty:
            fig_category = px.pie(
                stats['category_dist'],
                values='count',
                names='category',
                title='Inquiry Category Distribution',
                hole=0.4
            )
            fig_category.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_category, use_container_width=True)
        else:
            st.info("No category data available")
    
    with col2:
        # Department Distribution
        if not stats['dept_dist'].empty:
            fig_dept = px.bar(
                stats['dept_dist'],
                x='department',
                y='count',
                title='Department Routing Distribution',
                color='count',
                color_continuous_scale='Blues'
            )
            st.plotly_chart(fig_dept, use_container_width=True)
        else:
            st.info("No department data available")
    
    # Charts Row 2
    col1, col2 = st.columns(2)
    
    with col1:
        # Urgency Distribution
        if not stats['urgency_dist'].empty:
            urgency_order = ['low', 'medium', 'high', 'critical']
            stats['urgency_dist']['urgency'] = pd.Categorical(
                stats['urgency_dist']['urgency'],
                categories=urgency_order,
                ordered=True
            )
            stats['urgency_dist'] = stats['urgency_dist'].sort_values('urgency')
            
            fig_urgency = px.bar(
                stats['urgency_dist'],
                x='urgency',
                y='count',
                title='Urgency Level Distribution',
                color='urgency',
                color_discrete_map={
                    'low': '#90EE90',
                    'medium': '#FFD700',
                    'high': '#FF8C00',
                    'critical': '#FF0000'
                }
            )
            st.plotly_chart(fig_urgency, use_container_width=True)
        else:
            st.info("No urgency data available")
    
    with col2:
        # Sentiment Distribution
        if not stats['sentiment_dist'].empty:
            fig_sentiment = px.pie(
                stats['sentiment_dist'],
                values='count',
                names='sentiment',
                title='Sentiment Distribution',
                color='sentiment',
                color_discrete_map={
                    'positive': '#00D100',
                    'neutral': '#FFD700',
                    'negative': '#FF4444'
                }
            )
            st.plotly_chart(fig_sentiment, use_container_width=True)
        else:
            st.info("No sentiment data available")
    
    # Model Confidence Analysis
    st.header("🎯 Model Performance")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        avg_cat_conf = df['category_confidence'].mean() if len(df) > 0 else 0
        st.metric("Avg Category Confidence", f"{avg_cat_conf:.2%}")
    
    with col2:
        avg_sent_conf = df['sentiment_confidence'].mean() if len(df) > 0 else 0
        st.metric("Avg Sentiment Confidence", f"{avg_sent_conf:.2%}")
    
    with col3:
        avg_urg_conf = df['urgency_confidence'].mean() if len(df) > 0 else 0
        st.metric("Avg Urgency Confidence", f"{avg_urg_conf:.2%}")
    
    # Confidence Distribution
    if len(df) > 0:
        fig_confidence = go.Figure()
        fig_confidence.add_trace(go.Histogram(
            x=df['category_confidence'],
            name='Category',
            opacity=0.7,
            nbinsx=20
        ))
        fig_confidence.add_trace(go.Histogram(
            x=df['sentiment_confidence'],
            name='Sentiment',
            opacity=0.7,
            nbinsx=20
        ))
        fig_confidence.add_trace(go.Histogram(
            x=df['urgency_confidence'],
            name='Urgency',
            opacity=0.7,
            nbinsx=20
        ))
        
        fig_confidence.update_layout(
            title='Model Confidence Distribution',
            xaxis_title='Confidence Score',
            yaxis_title='Count',
            barmode='overlay'
        )
        st.plotly_chart(fig_confidence, use_container_width=True)
    
    # Recent Inquiries Table
    st.header("📋 Recent Inquiries")
    
    if len(df) > 0:
        # Format dataframe for display
        display_df = df[[
            'timestamp', 'subject', 'category', 'urgency',
            'sentiment', 'department', 'priority_score', 'escalated'
        ]].copy()
        
        display_df['timestamp'] = pd.to_datetime(display_df['timestamp'])
        display_df = display_df.sort_values('timestamp', ascending=False)
        
        # Add row numbers for selection
        display_df_with_index = display_df.reset_index(drop=True)
        display_df_with_index.index = display_df_with_index.index + 1
        
        # Show table with expandable details
        st.dataframe(
            display_df_with_index.head(50),
            use_container_width=True,
            height=400
        )
        
        # Inquiry Details Section
        st.subheader("🔍 Inquiry Details")
        
        # Create a selectbox for inquiry selection
        inquiry_options = [f"#{i}: {row['subject'][:50]}..." for i, row in display_df_with_index.head(50).iterrows()]
        
        if inquiry_options:
            selected_idx = st.selectbox(
                "Select an inquiry to view details:",
                range(len(inquiry_options)),
                format_func=lambda x: inquiry_options[x]
            )
            
            if selected_idx is not None:
                selected_inquiry = display_df_with_index.iloc[selected_idx]
                # The display_df_with_index index is 1-based, but we need 0-based for the original df
                original_idx = selected_inquiry.name - 1
                
                # Get full inquiry details from the original dataframe
                full_inquiry = df.iloc[original_idx]
                
                # Display inquiry details in columns
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown("### 📧 Inquiry Content")
                    st.markdown(f"**Subject:** {full_inquiry['subject']}")
                    st.markdown(f"**Body:**")
                    st.text_area("", full_inquiry['body'], height=200, disabled=True)
                
                with col2:
                    st.markdown("### 📊 Analysis Results")
                    st.markdown(f"**Category:** {full_inquiry['category']}")
                    st.markdown(f"**Confidence:** {full_inquiry['category_confidence']:.2%}")
                    
                    st.markdown(f"**Sentiment:** {full_inquiry['sentiment']}")
                    st.markdown(f"**Confidence:** {full_inquiry['sentiment_confidence']:.2%}")
                    
                    st.markdown(f"**Urgency:** {full_inquiry['urgency']}")
                    st.markdown(f"**Confidence:** {full_inquiry['urgency_confidence']:.2%}")
                
                # Routing Information
                col3, col4 = st.columns(2)
                
                with col3:
                    st.markdown("### 🎯 Routing Decision")
                    st.markdown(f"**Department:** {full_inquiry['department']}")
                    st.markdown(f"**Consultant:** {full_inquiry['assigned_consultant']}")
                    st.markdown(f"**Priority Score:** {full_inquiry['priority_score']:.1f}")
                
                with col4:
                    st.markdown("### 📋 Metadata")
                    st.markdown(f"**Sender:** {full_inquiry['sender_email']}")
                    st.markdown(f"**Timestamp:** {full_inquiry['timestamp']}")
                    st.markdown(f"**Escalated:** {'Yes' if full_inquiry['escalated'] else 'No'}")
                
                # Status indicators
                if full_inquiry['escalated']:
                    st.warning("⚠️ This inquiry has been escalated!")
                
                if full_inquiry['urgency'] == 'critical':
                    st.error("🚨 Critical urgency level!")
                
                if full_inquiry['sentiment'] == 'negative':
                    st.info("😞 Negative sentiment detected")
    else:
        st.info("No inquiries to display")
    
    # Refresh button
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    # API Ingestion Section
    st.markdown("---")
    st.subheader("🚀 Submit New Inquiry via API")
    
    with st.form("api_inquiry_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            subject = st.text_input("Subject", placeholder="Enter inquiry subject...")
            sender_email = st.text_input("Sender Email", placeholder="user@example.com")
        
        with col2:
            body = st.text_area("Message Body", placeholder="Enter inquiry details...", height=100)
            sender_name = st.text_input("Sender Name (optional)", placeholder="John Doe")
        
        submitted = st.form_submit_button("Submit Inquiry", type="primary")
        
        if submitted:
            if subject and body and sender_email:
                try:
                    import requests
                    
                    # Prepare API request
                    api_data = {
                        "subject": subject,
                        "body": body,
                        "sender_email": sender_email,
                        "sender_name": sender_name if sender_name else None
                    }
                    
                    # Submit to API
                    response = requests.post(
                        "http://api:8000/api/v1/inquiries/submit",
                        json=api_data,
                        timeout=10
                    )
                    
                    if response.status_code == 201:
                        result = response.json()
                        st.success("✅ Inquiry submitted successfully!")
                        
                        # Show processing results
                        with st.expander("Processing Results"):
                            st.json(result["data"])
                            
                        # Show success message - user can manually refresh if needed
                        st.info("🔄 Dashboard will refresh automatically. If not, please refresh manually.")
                    else:
                        st.error(f"❌ API Error: {response.status_code} - {response.text}")
                        
                except Exception as e:
                    st.error(f"❌ Submission failed: {str(e)}")
            else:
                st.warning("⚠️ Please fill in all required fields (Subject, Body, Sender Email)")

    # Footer
    st.markdown("---")
    st.markdown(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.info("Make sure the database is running and accessible.")
    
    # Show connection details for debugging
    with st.expander("Connection Details"):
        st.code(os.getenv("DATABASE_URL", "Not set"))

