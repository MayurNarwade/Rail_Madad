# frontend/streamlit_app.py - UPDATED with correct status check
import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
from datetime import datetime
import io
import time

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

# Page configuration
st.set_page_config(
    page_title="Rail Madad AI System",
    page_icon="🚆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .complaint-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 5px solid #1f77b4;
    }
    .urgent {
        border-left-color: #ff4b4b !important;
    }
    .high {
        border-left-color: #ffa500 !important;
    }
    .medium {
        border-left-color: #ffcc00 !important;
    }
    .low {
        border-left-color: #00cc66 !important;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
    }
    .api-status-connected {
        background-color: #d4edda;
        color: #155724;
        padding: 0.5rem;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
    }
    .api-status-disconnected {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.5rem;
        border-radius: 5px;
        border: 1px solid #f5c6cb;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """Initialize session state variables"""
    if 'complaints' not in st.session_state:
        st.session_state.complaints = []
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'api_status' not in st.session_state:
        st.session_state.api_status = "unknown"

def check_api_status():
    """Check if backend API is available - FIXED endpoint"""
    try:
        # Try multiple endpoints to ensure API is working
        endpoints_to_check = [
            "/health",
            "/"
        ]
        
        for endpoint in endpoints_to_check:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=3)
            if response.status_code == 200:
                st.session_state.api_status = "connected"
                return True
        
        # If specific endpoints fail, try the API root
        response = requests.get(f"{API_BASE_URL}/health", timeout=3)
        if response.status_code == 200:
            st.session_state.api_status = "connected"
            return True
            
        st.session_state.api_status = "error"
        return False
        
    except requests.exceptions.ConnectionError:
        st.session_state.api_status = "disconnected"
        return False
    except Exception as e:
        st.session_state.api_status = "error"
        return False

def display_api_status():
    """Display API status with appropriate styling"""
    status = st.session_state.api_status
    
    if status == "connected":
        st.markdown('<div class="api-status-connected">✅ Backend API is connected and ready</div>', unsafe_allow_html=True)
    elif status == "disconnected":
        st.markdown('<div class="api-status-disconnected">❌ Backend API is not available. Make sure the backend server is running on port 8000.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="api-status-disconnected">⚠️ Unable to determine API status</div>', unsafe_allow_html=True)
    
    return status == "connected"

def complaint_submission_page():
    """Complaint submission page"""
    st.markdown('<div class="main-header">🚆 Rail Madad - Submit Complaint</div>', unsafe_allow_html=True)
    
    # API status indicator
    display_api_status()
    
    if not check_api_status():
        st.error("""
        **Backend server is not running. Please start it with:**
        ```bash
        cd backend
        python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
        ```
        """)
        return
    
    # Initialize session state for quick categories if not exists
    if 'quick_category_selected' not in st.session_state:
        st.session_state.quick_category_selected = None
    if 'quick_category_text' not in st.session_state:
        st.session_state.quick_category_text = ""
    
    # Quick category selection section - MOVED OUTSIDE THE FORM
    st.subheader("📋 Quick Categories")
    st.write("Select a category to pre-fill the description template:")
    
    category_templates = {
        "cleanliness": "🚮 Cleanliness Issue: Dirty or unclean area needs immediate attention. Location: ",
        "damage": "🔧 Damage Report: Broken or damaged equipment requiring repair. Location: ",
        "safety": "🚨 Safety Hazard: Potential safety risk that needs urgent addressing. Location: ",
        "facility": "🏢 Facility Issue: Problem with station or train facilities. Location: ",
        "electrical": "⚡ Electrical Problem: Electrical issue requiring technician. Location: ",
        "sanitation": "🚽 Sanitation Problem: Restroom or hygiene related issue. Location: ",
        "crowding": "👥 Overcrowding: Excessive crowding causing inconvenience. Location: ",
        "other": "❓ Other Issue: Please describe the problem. Location: "
    }
    
    # First row of buttons
    quick_categories1 = st.columns(4)
    
    with quick_categories1[0]:
        if st.button("🚮 Cleanliness", use_container_width=True, key="cleanliness_btn"):
            st.session_state.quick_category_selected = "cleanliness"
            st.session_state.quick_category_text = category_templates["cleanliness"]
            st.rerun()
    
    with quick_categories1[1]:
        if st.button("🔧 Damage", use_container_width=True, key="damage_btn"):
            st.session_state.quick_category_selected = "damage"
            st.session_state.quick_category_text = category_templates["damage"]
            st.rerun()
    
    with quick_categories1[2]:
        if st.button("🚨 Safety", use_container_width=True, key="safety_btn"):
            st.session_state.quick_category_selected = "safety"
            st.session_state.quick_category_text = category_templates["safety"]
            st.rerun()
    
    with quick_categories1[3]:
        if st.button("🏢 Facilities", use_container_width=True, key="facility_btn"):
            st.session_state.quick_category_selected = "facility"
            st.session_state.quick_category_text = category_templates["facility"]
            st.rerun()
    
    # Second row of buttons
    quick_categories2 = st.columns(4)
    
    with quick_categories2[0]:
        if st.button("⚡ Electrical", use_container_width=True, key="electrical_btn"):
            st.session_state.quick_category_selected = "electrical"
            st.session_state.quick_category_text = category_templates["electrical"]
            st.rerun()
    
    with quick_categories2[1]:
        if st.button("🚽 Sanitation", use_container_width=True, key="sanitation_btn"):
            st.session_state.quick_category_selected = "sanitation"
            st.session_state.quick_category_text = category_templates["sanitation"]
            st.rerun()
    
    with quick_categories2[2]:
        if st.button("👥 Crowding", use_container_width=True, key="crowding_btn"):
            st.session_state.quick_category_selected = "crowding"
            st.session_state.quick_category_text = category_templates["crowding"]
            st.rerun()
    
    with quick_categories2[3]:
        if st.button("❓ Other", use_container_width=True, key="other_btn"):
            st.session_state.quick_category_selected = "other"
            st.session_state.quick_category_text = category_templates["other"]
            st.rerun()
    
    # Show selected category and clear button
    if st.session_state.quick_category_selected:
        st.success(f"✅ Quick category selected: {st.session_state.quick_category_selected.title()}")
        
        clear_col1, clear_col2 = st.columns([3, 1])
        with clear_col2:
            if st.button("🗑️ Clear Category", use_container_width=True, key="clear_category_btn"):
                st.session_state.quick_category_selected = None
                st.session_state.quick_category_text = ""
                st.rerun()
    
    st.markdown("---")
    
    # Complaint form - BUTTONS REMOVED FROM HERE
    with st.form("complaint_form", clear_on_submit=True):
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📷 Upload Media")
            uploaded_file = st.file_uploader(
                "Upload Image or Video",
                type=['jpg', 'jpeg', 'png', 'mp4'],
                help="Upload clear photos or videos of the issue (Max 10MB)"
            )
            
            if uploaded_file:
                file_size = len(uploaded_file.getvalue()) / 1024 / 1024  # Size in MB
                st.info(f"File: {uploaded_file.name} ({file_size:.2f} MB)")
                
                if uploaded_file.type.startswith('image'):
                    st.image(uploaded_file, caption="Preview", use_column_width=True)
                else:
                    st.video(uploaded_file)
            
        with col2:
            st.subheader("📝 Complaint Details")
            description = st.text_area(
                "Description *",
                placeholder="Describe the issue in detail...\nExample: 'Broken seat near window 5, coach B2. Needs urgent repair.'",
                height=150,
                help="Required: Include location, severity, and details",
                value=st.session_state.quick_category_text
            )
            
            # Additional form fields can be added here
            st.subheader("ℹ️ Additional Information")
            location = st.text_input(
                "Specific Location (Optional)",
                placeholder="e.g., Coach B2, Seat 15, Platform 3, etc.",
                help="Where exactly is the issue located?"
            )
            
            # Add location to description if provided
            if location and description and not description.endswith(location):
                description += f" Location: {location}"
        
        submitted = st.form_submit_button("📤 Submit Complaint", type="primary", use_container_width=True)
        
        if submitted:
            if not uploaded_file:
                st.error("❌ Please upload a file (image or video)")
                return
                
            if not description.strip():
                st.error("❌ Please provide a description of the issue")
                return
            
            # Show progress
            with st.spinner("🔄 Processing your complaint..."):
                try:
                    # Prepare form data
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    data = {"description": description}
                    
                    response = requests.post(
                        f"{API_BASE_URL}/complaints/submit",
                        files=files,
                        data=data,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Success message
                        st.markdown(f"""
                        <div class="success-message">
                            <h3>✅ Complaint Submitted Successfully!</h3>
                            <p><strong>Complaint ID:</strong> {result['id']}</p>
                            <p><strong>Category:</strong> {result['category'].title()}</p>
                            <p><strong>Urgency:</strong> {result['urgency'].title()}</p>
                            <p><strong>Department:</strong> {result['department']}</p>
                            <p><strong>Processing Time:</strong> {result['processing_time']:.2f} seconds</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Show acknowledgment
                        st.info(f"**Acknowledgment:** {result['acknowledgment']}")
                        
                        # Clear quick category after successful submission
                        st.session_state.quick_category_selected = None
                        st.session_state.quick_category_text = ""
                        
                    else:
                        st.error(f"❌ Error submitting complaint: {response.status_code} - {response.text}")
                        
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to backend server. Make sure it's running on port 8000.")
                except requests.exceptions.Timeout:
                    st.error("⏰ Request timeout. The server is taking too long to respond.")
                except Exception as e:
                    st.error(f"❌ Unexpected error: {str(e)}")

def chat_page():
    """AI Chatbot page - FIXED VERSION"""
    st.markdown('<div class="main-header">💬 Rail Madad - AI Assistant</div>', unsafe_allow_html=True)
    
    display_api_status()
    
    if not check_api_status():
        st.error("Backend API is not available.")
        return
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm Rail Madad AI assistant. How can I help you with train-related issues today?"}
        ]
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response - FIXED: Proper error handling
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/chat/send",
                        json={"message": prompt},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        response_text = result["response"]
                        
                        # Display the actual AI response
                        st.markdown(response_text)
                        st.session_state.messages.append({"role": "assistant", "content": response_text})
                        
                    else:
                        # Show actual error instead of "unavailable"
                        error_msg = f"⚠️ API returned error {response.status_code}. Please try again."
                        st.markdown(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                        
                except requests.exceptions.ConnectionError:
                    error_msg = "❌ Cannot connect to backend server. Please make sure it's running."
                    st.markdown(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    
                except requests.exceptions.Timeout:
                    error_msg = "⏰ Request timeout. Please try again in a moment."
                    st.markdown(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    
                except Exception as e:
                    # Show the actual error for debugging
                    error_msg = f"🔧 Technical issue: {str(e)}. Please try the complaint form as backup."
                    st.markdown(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    # Clear chat button
    if st.button("Clear Chat History", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm Rail Madad AI assistant. How can I help you today?"}
        ]
        st.rerun()

def dashboard_page():
    """Admin Dashboard page"""
    st.markdown('<div class="main-header">📊 Rail Madad - Admin Dashboard</div>', unsafe_allow_html=True)
    
    # Password protection (simple)
    password = st.text_input("Enter Admin Password:", type="password", key="admin_pass")
    if password != "admin123":
        st.warning("🔒 Please enter the admin password to access the dashboard")
        return
    
    display_api_status()
    
    if not check_api_status():
        st.error("Backend API is not available.")
        return
    
    try:
        # Get trends data
        response = requests.get(f"{API_BASE_URL}/trends/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Complaints", data["total_complaints"])
            with col2:
                st.metric("Avg Accuracy", f"{data['metrics']['avg_accuracy']:.1%}")
            with col3:
                st.metric("Avg Processing Time", f"{data['metrics']['avg_processing_time']:.2f}s")
            with col4:
                st.metric("Total Processed", data["metrics"]["total_processed"])
            
            # Trends chart
            if data["trends"]:
                st.subheader("📈 Complaint Trends by Category")
                df = pd.DataFrame(data["trends"])
                fig = px.bar(df, x='category', y='count', color='category',
                           title="Complaints by Category")
                st.plotly_chart(fig, use_container_width=True)
                
                # Display trends table
                st.subheader("📋 Detailed Breakdown")
                st.dataframe(df, use_container_width=True)
                
                # Export button
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Export as CSV",
                    data=csv,
                    file_name="rail_madad_trends.csv",
                    mime="text/csv"
                )
            else:
                st.info("No complaint data available yet.")
                
        else:
            st.error("Error fetching dashboard data")
            
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")
    
    # Recent complaints section with status update functionality
    st.subheader("🕒 Recent Complaints - Status Management")
    
    # Refresh button to get latest data
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
    
    try:
        complaints_response = requests.get(f"{API_BASE_URL}/complaints/list?limit=20", timeout=10)
        if complaints_response.status_code == 200:
            complaints_data = complaints_response.json()
            complaints = complaints_data.get("complaints", [])
            
            if complaints:
                # Display complaints with status update functionality
                for complaint in complaints:
                    # Use the database ID (id) not complaint_id for updates
                    complaint_id = complaint['id']
                    current_status = complaint.get('status', 'pending')
                    
                    # Create a unique key for each complaint
                    status_key = f"status_{complaint_id}"
                    update_key = f"update_{complaint_id}"
                    
                    # Status color coding
                    status_colors = {
                        'pending': '#ff4b4b',
                        'in_progress': '#ffa500', 
                        'resolved': '#00cc66',
                        'closed': '#1f77b4'
                    }
                    
                    status_color = status_colors.get(current_status, '#666666')
                    
                    # Display complaint card
                    with st.container():
                        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                        
                        with col1:
                            st.write(f"**ID:** {complaint_id}")
                            st.write(f"**Description:** {complaint.get('description', 'N/A')[:100]}...")
                            
                        with col2:
                            st.write(f"**Category:** {complaint.get('category', 'N/A').title()}")
                            st.write(f"**Urgency:** {complaint.get('urgency', 'N/A').title()}")
                            
                        with col3:
                            st.write(f"**Department:** {complaint.get('department', 'N/A')}")
                            st.write(f"**Submitted:** {complaint.get('timestamp', 'N/A')[:16]}")
                            
                        with col4:
                            # Current status display
                            st.markdown(f"**Current Status:** <span style='color: {status_color}; font-weight: bold'>{current_status.replace('_', ' ').title()}</span>", unsafe_allow_html=True)
                            
                            # Status update section
                            status_options = ['pending', 'in_progress', 'resolved', 'closed']
                            new_status = st.selectbox(
                                "Change to:",
                                options=status_options,
                                index=status_options.index(current_status) if current_status in status_options else 0,
                                key=status_key,
                                label_visibility="collapsed"
                            )
                            
                            # Update button
                            if st.button("Update", key=update_key, use_container_width=True):
                                if new_status != current_status:
                                    with st.spinner("Updating status..."):
                                        try:
                                            update_response = requests.put(
                                                f"{API_BASE_URL}/complaints/status/{complaint_id}",
                                                json={"status": new_status},
                                                timeout=10
                                            )
                                            
                                            if update_response.status_code == 200:
                                                st.success(f"✅ Status updated to {new_status.replace('_', ' ').title()}!")
                                                # Add small delay to show success message
                                                time.sleep(1)
                                                st.rerun()
                                            else:
                                                st.error(f"❌ Failed to update status: {update_response.text}")
                                        except Exception as e:
                                            st.error(f"❌ Error updating status: {str(e)}")
                                else:
                                    st.warning("Status is already set to this value")
                        
                        st.markdown("---")
                
                # Display all complaints in a compact table view
                st.subheader("📋 All Complaints Overview")
                
                # Create DataFrame for table view
                df_complaints = pd.DataFrame(complaints)
                
                # Add status color coding function
                def color_status(val):
                    if val == 'resolved':
                        return 'color: #155724; background-color: #d4edda;'
                    elif val == 'in_progress':
                        return 'color: #856404; background-color: #fff3cd;'
                    elif val == 'closed':
                        return 'color: #0c5460; background-color: #d1ecf1;'
                    else:  # pending
                        return 'color: #721c24; background-color: #f8d7da;'
                
                if not df_complaints.empty:
                    # Display important columns
                    display_columns = ['id', 'category', 'urgency', 'status', 'timestamp']
                    available_columns = [col for col in display_columns if col in df_complaints.columns]
                    
                    styled_df = df_complaints[available_columns].copy()
                    styled_df['timestamp'] = styled_df['timestamp'].str[:19]  # Format timestamp
                    
                    # Apply styling
                    styled_df = styled_df.style.applymap(color_status, subset=['status'])
                    st.dataframe(styled_df, use_container_width=True, height=300)
                    
                    # Show statistics
                    st.subheader("📊 Status Statistics")
                    status_counts = df_complaints['status'].value_counts()
                    col1, col2, col3, col4 = st.columns(4)
                    
                    status_info = {
                        'pending': ('⏳ Pending', '#ff4b4b'),
                        'in_progress': ('🔄 In Progress', '#ffa500'),
                        'resolved': ('✅ Resolved', '#00cc66'),
                        'closed': ('📋 Closed', '#1f77b4')
                    }
                    
                    for i, (status, count) in enumerate(status_counts.items()):
                        status_name, color = status_info.get(status, (status.title(), '#666666'))
                        with [col1, col2, col3, col4][i % 4]:
                            st.metric(status_name, count)
                
            else:
                st.info("No complaints found in the system. Submit some complaints first!")
        else:
            st.error("Error fetching complaints list")
    except Exception as e:
        st.error(f"Error loading complaints: {str(e)}")
    
    # Bulk status update section
    st.subheader("🔄 Bulk Status Management")
    
    try:
        # Get current complaints for bulk operations
        bulk_response = requests.get(f"{API_BASE_URL}/complaints/list?limit=100", timeout=10)
        if bulk_response.status_code == 200:
            bulk_complaints = bulk_response.json().get("complaints", [])
            
            if bulk_complaints:
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    current_status_filter = st.selectbox(
                        "Filter by current status:",
                        options=['all', 'pending', 'in_progress', 'resolved', 'closed'],
                        key="filter_status"
                    )
                
                with col2:
                    new_bulk_status = st.selectbox(
                        "Set new status:",
                        options=['pending', 'in_progress', 'resolved', 'closed'],
                        key="bulk_status"
                    )
                
                with col3:
                    if st.button("Apply Bulk Update", use_container_width=True):
                        if current_status_filter == 'all':
                            st.warning(f"This will update ALL {len(bulk_complaints)} complaints to {new_bulk_status}.")
                            if st.button("Confirm Update All", type="primary"):
                                update_all_complaints(new_bulk_status)
                        else:
                            filtered_complaints = [c for c in bulk_complaints if c.get('status') == current_status_filter]
                            if filtered_complaints:
                                st.warning(f"This will update {len(filtered_complaints)} complaints from {current_status_filter} to {new_bulk_status}.")
                                if st.button("Confirm Update", type="primary"):
                                    update_complaints_by_status(current_status_filter, new_bulk_status)
                            else:
                                st.warning(f"No complaints found with status: {current_status_filter}")
            else:
                st.info("No complaints available for bulk operations")
        else:
            st.error("Error fetching complaints for bulk operations")
    except Exception as e:
        st.error(f"Error in bulk operations: {str(e)}")

def update_complaints_by_status(current_status, new_status):
    """Update all complaints with a specific status"""
    try:
        response = requests.get(f"{API_BASE_URL}/complaints/list?limit=100", timeout=10)
        if response.status_code == 200:
            complaints = response.json().get("complaints", [])
            complaints_to_update = [c for c in complaints if c.get('status') == current_status]
            
            if not complaints_to_update:
                st.warning(f"No complaints found with status: {current_status}")
                return
            
            success_count = 0
            progress_bar = st.progress(0)
            total_complaints = len(complaints_to_update)
            
            for i, complaint in enumerate(complaints_to_update):
                update_response = requests.put(
                    f"{API_BASE_URL}/complaints/status/{complaint['id']}",
                    json={"status": new_status},
                    timeout=10
                )
                if update_response.status_code == 200:
                    success_count += 1
                
                # Update progress bar
                progress_bar.progress((i + 1) / total_complaints)
            
            st.success(f"✅ Updated {success_count}/{total_complaints} complaints from {current_status} to {new_status}")
            time.sleep(2)
            st.rerun()
        else:
            st.error("Error fetching complaints for bulk update")
    except Exception as e:
        st.error(f"Error during bulk update: {str(e)}")

def update_all_complaints(new_status):
    """Update all complaints to a new status"""
    try:
        response = requests.get(f"{API_BASE_URL}/complaints/list?limit=100", timeout=10)
        if response.status_code == 200:
            complaints = response.json().get("complaints", [])
            
            if not complaints:
                st.warning("No complaints found to update")
                return
            
            success_count = 0
            progress_bar = st.progress(0)
            total_complaints = len(complaints)
            
            for i, complaint in enumerate(complaints):
                update_response = requests.put(
                    f"{API_BASE_URL}/complaints/status/{complaint['id']}",
                    json={"status": new_status},
                    timeout=10
                )
                if update_response.status_code == 200:
                    success_count += 1
                
                # Update progress bar
                progress_bar.progress((i + 1) / total_complaints)
            
            st.success(f"✅ Updated {success_count}/{total_complaints} complaints to {new_status}")
            time.sleep(2)
            st.rerun()
        else:
            st.error("Error fetching complaints for bulk update")
    except Exception as e:
        st.error(f"Error during bulk update: {str(e)}")

def status_page():
    """Check complaint status page"""
    st.markdown('<div class="main-header">🔍 Rail Madad - Check Status</div>', unsafe_allow_html=True)
    
    display_api_status()
    
    if not check_api_status():
        st.error("Backend API is not available.")
        return
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Check Complaint Status")
        complaint_id = st.number_input("Enter Complaint ID:", min_value=1, value=1, key="status_id")
        
        if st.button("Check Status", use_container_width=True, key="check_status_btn"):
            try:
                response = requests.get(f"{API_BASE_URL}/complaints/status/{complaint_id}", timeout=10)
                if response.status_code == 200:
                    status_data = response.json()
                    
                    # Display status with color coding
                    status = status_data.get('status', 'pending')
                    status_colors = {
                        'pending': 'red',
                        'in_progress': 'orange',
                        'resolved': 'green',
                        'closed': 'blue'
                    }
                    status_color = status_colors.get(status, 'gray')
                    
                    st.success(f"✅ Complaint Found!")
                    st.markdown(f"**Status:** <span style='color: {status_color}; font-weight: bold'>{status.replace('_', ' ').title()}</span>", unsafe_allow_html=True)
                    st.json(status_data)
                    
                elif response.status_code == 404:
                    st.error("❌ Complaint not found. Please check the ID.")
                else:
                    st.error("Error fetching complaint status")
                    
            except Exception as e:
                st.error(f"Error checking status: {str(e)}")
    
    with col2:
        st.subheader("Recent Complaints")
        try:
            response = requests.get(f"{API_BASE_URL}/complaints/list?limit=10", timeout=10)
            if response.status_code == 200:
                complaints = response.json().get("complaints", [])
                
                if complaints:
                    # Create a simplified view
                    simplified_complaints = []
                    for complaint in complaints:
                        simplified_complaints.append({
                            'id': complaint['id'],
                            'category': complaint.get('category', 'N/A').title(),
                            'urgency': complaint.get('urgency', 'N/A').title(),
                            'status': complaint.get('status', 'pending').replace('_', ' ').title()
                        })
                    
                    df = pd.DataFrame(simplified_complaints)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No complaints found in the system.")
            else:
                st.error("Error fetching complaints list")
        except:
            st.info("Could not load complaints list.")

def main():
    """Main application"""
    init_session_state()
    
    # Sidebar navigation
    st.sidebar.title("🚆 Rail Madad AI")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "Navigation",
        ["Submit Complaint", "AI Chat", "Check Status", "Admin Dashboard"],
        index=0
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info("""
    **Rail Madad AI System**
    
    - Submit complaints with photos/videos
    - AI-powered categorization
    - Real-time status tracking
    - Analytics dashboard
    
    **Backend Status:**
    """)
    
    # Display API status in sidebar
    check_api_status()
    status_text = "✅ Connected" if st.session_state.api_status == "connected" else "❌ Disconnected"
    st.sidebar.write(f"API: {status_text}")
    
    # Display selected page
    if page == "Submit Complaint":
        complaint_submission_page()
    elif page == "AI Chat":
        chat_page()
    elif page == "Check Status":
        status_page()
    elif page == "Admin Dashboard":
        dashboard_page()

if __name__ == "__main__":
    main()