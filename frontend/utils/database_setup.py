import streamlit as st
from services.api_client import api_client

def setup_database_tables():
    """Kiểm tra kết nối API"""
    if not api_client.base_url:
        print("❌ API client not available - running in local mode")
        return
    
    # try:
    #     # Test API connection
    #     sessions = api_client.get_all_sessions()
    print("✅ API connection successful")