import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elogbookagu.settings')
django.setup()

# Import Django models
from admin_section.models import Department, ActivityType, LogYear, CoreDiaProSession
from accounts.models import Student, Doctor, Staff, CustomUser
from student_section.models import StudentLogFormModel, SupportTicket

# Set page config
st.set_page_config(
    page_title="ElogBook Admin Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .dashboard-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        color: #1e3a8a;
        text-align: center;
    }
    .dashboard-subtitle {
        font-size: 1.2rem;
        font-weight: 400;
        margin-bottom: 2rem;
        color: #6b7280;
        text-align: center;
    }
    .metric-card {
        background-color: white;
        border-radius: 0.5rem;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #2563eb;
    }
    .metric-label {
        font-size: 1rem;
        color: #6b7280;
        margin-top: 0.5rem;
    }
    .chart-container {
        background-color: white;
        border-radius: 0.5rem;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        margin-top: 1.5rem;
    }
    .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: #1e3a8a;
    }
</style>
""", unsafe_allow_html=True)

# Dashboard title
st.markdown('<div class="dashboard-title">ElogBook Admin Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="dashboard-subtitle">Real-time analytics and insights for administrators</div>', unsafe_allow_html=True)

# Sidebar filters
st.sidebar.title("Filters")

# Department filter
departments = Department.objects.all()
department_options = ["All Departments"] + [dept.name for dept in departments]
selected_department = st.sidebar.selectbox("Select Department", department_options)

# Date range filter
today = datetime.now().date()
start_date = st.sidebar.date_input("Start Date", today - timedelta(days=30))
end_date = st.sidebar.date_input("End Date", today)

# Apply filters
if selected_department == "All Departments":
    logs = StudentLogFormModel.objects.filter(
        date__range=[start_date, end_date]
    )
else:
    department = Department.objects.get(name=selected_department)
    logs = StudentLogFormModel.objects.filter(
        department=department,
        date__range=[start_date, end_date]
    )

# Key metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{Student.objects.count()}</div>', unsafe_allow_html=True)
    st.markdown('<div class="metric-label">Total Students</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{Doctor.objects.count()}</div>', unsafe_allow_html=True)
    st.markdown('<div class="metric-label">Total Doctors</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{ActivityType.objects.count()}</div>', unsafe_allow_html=True)
    st.markdown('<div class="metric-label">Activity Types</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{logs.count()}</div>', unsafe_allow_html=True)
    st.markdown('<div class="metric-label">Total Logs</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Review status chart
st.markdown('<div class="chart-container">', unsafe_allow_html=True)
st.markdown('<div class="section-title">Review Status</div>', unsafe_allow_html=True)

approved_logs = logs.filter(is_reviewed=True, is_approved=True).count()
rejected_logs = logs.filter(is_reviewed=True, is_approved=False).count()
pending_logs = logs.filter(is_reviewed=False).count()

review_data = pd.DataFrame({
    'Status': ['Approved', 'Rejected', 'Pending'],
    'Count': [approved_logs, rejected_logs, pending_logs]
})

fig = px.pie(
    review_data, 
    values='Count', 
    names='Status',
    color='Status',
    color_discrete_map={
        'Approved': '#10B981',  # Green
        'Rejected': '#EF4444',  # Red
        'Pending': '#F59E0B'    # Amber
    },
    hole=0.4
)
fig.update_layout(
    margin=dict(l=20, r=20, t=30, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
)
st.plotly_chart(fig, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# Department performance
st.markdown('<div class="chart-container">', unsafe_allow_html=True)
st.markdown('<div class="section-title">Department Performance</div>', unsafe_allow_html=True)

dept_data = []
for dept in departments:
    dept_logs = StudentLogFormModel.objects.filter(
        department=dept,
        date__range=[start_date, end_date]
    )
    approved = dept_logs.filter(is_reviewed=True, is_approved=True).count()
    rejected = dept_logs.filter(is_reviewed=True, is_approved=False).count()
    pending = dept_logs.filter(is_reviewed=False).count()
    
    dept_data.append({
        'Department': dept.name,
        'Approved': approved,
        'Rejected': rejected,
        'Pending': pending,
        'Total': approved + rejected + pending
    })

dept_df = pd.DataFrame(dept_data)
if not dept_df.empty:
    # Sort by total logs
    dept_df = dept_df.sort_values('Total', ascending=False)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=dept_df['Department'],
        y=dept_df['Approved'],
        name='Approved',
        marker_color='#10B981'
    ))
    fig.add_trace(go.Bar(
        x=dept_df['Department'],
        y=dept_df['Rejected'],
        name='Rejected',
        marker_color='#EF4444'
    ))
    fig.add_trace(go.Bar(
        x=dept_df['Department'],
        y=dept_df['Pending'],
        name='Pending',
        marker_color='#F59E0B'
    ))
    
    fig.update_layout(
        barmode='stack',
        xaxis={'categoryorder':'total descending'},
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No department data available for the selected date range.")
st.markdown('</div>', unsafe_allow_html=True)

# Student performance search
st.markdown('<div class="chart-container">', unsafe_allow_html=True)
st.markdown('<div class="section-title">Student Performance Search</div>', unsafe_allow_html=True)

student_search = st.text_input("Search by Name, ID or Email")

if student_search:
    # Search for student
    students = Student.objects.filter(
        student_id__icontains=student_search
    ) | Student.objects.filter(
        user__first_name__icontains=student_search
    ) | Student.objects.filter(
        user__last_name__icontains=student_search
    ) | Student.objects.filter(
        user__email__icontains=student_search
    )
    
    if students:
        student = students.first()
        st.subheader(f"Performance for {student.user.get_full_name()} (ID: {student.student_id})")
        
        # Get student logs
        student_logs = StudentLogFormModel.objects.filter(student=student)
        
        # Performance metrics
        approved = student_logs.filter(is_reviewed=True, is_approved=True).count()
        rejected = student_logs.filter(is_reviewed=True, is_approved=False).count()
        pending = student_logs.filter(is_reviewed=False).count()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Approved Logs", approved)
        with col2:
            st.metric("Pending Logs", pending)
        with col3:
            st.metric("Rejected Logs", rejected)
        
        # Department performance
        dept_data = []
        for dept in departments:
            dept_logs = student_logs.filter(department=dept)
            approved = dept_logs.filter(is_reviewed=True, is_approved=True).count()
            rejected = dept_logs.filter(is_reviewed=True, is_approved=False).count()
            pending = dept_logs.filter(is_reviewed=False).count()
            total = approved + rejected + pending
            
            if total > 0:
                dept_data.append({
                    'Department': dept.name,
                    'Approved': approved,
                    'Rejected': rejected,
                    'Pending': pending,
                    'Total': total
                })
        
        if dept_data:
            dept_df = pd.DataFrame(dept_data)
            fig = px.bar(
                dept_df, 
                x='Department', 
                y=['Approved', 'Rejected', 'Pending'],
                title="Performance by Department",
                barmode='stack',
                color_discrete_map={
                    'Approved': '#10B981',
                    'Rejected': '#EF4444',
                    'Pending': '#F59E0B'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Show department details table
            st.subheader("Department Details")
            st.dataframe(dept_df)
        else:
            st.info("No department data available for this student.")
    else:
        st.warning(f"No student found with search term: {student_search}")
else:
    st.info("Enter a student name, ID, or email to view their performance.")
st.markdown('</div>', unsafe_allow_html=True)

# Recent logs table
st.markdown('<div class="chart-container">', unsafe_allow_html=True)
st.markdown('<div class="section-title">Recent Logs</div>', unsafe_allow_html=True)

recent_logs = logs.order_by('-date')[:10]
if recent_logs:
    log_data = []
    for log in recent_logs:
        log_data.append({
            'Student': log.student.user.get_full_name(),
            'Student ID': log.student.student_id,
            'Date': log.date,
            'Department': log.department.name,
            'Activity': log.activity_type.name,
            'Status': 'Approved' if log.is_reviewed and log.is_approved else 'Rejected' if log.is_reviewed else 'Pending'
        })
    
    log_df = pd.DataFrame(log_data)
    st.dataframe(log_df, use_container_width=True)
else:
    st.info("No logs available for the selected filters.")
st.markdown('</div>', unsafe_allow_html=True)

# Run this script with: streamlit run streamlit_dashboard.py
