import streamlit as st
from utils import workflow_analyzer

def init_state():
    if 'workflow_response' not in st.session_state:
        st.session_state.workflow_response = None

def set_response(response):
    st.session_state.workflow_response = response
    # Also update the workflow analyzer
    workflow_analyzer.set_workflow_response(response)

def get_response():
    # First try to get from workflow analyzer
    response = workflow_analyzer.get_workflow_response()
    if response is None and 'workflow_response' in st.session_state:
        # Fall back to session state if available
        response = st.session_state.workflow_response
    return response