
# Add the sidebar toggle button with a clear icon
import streamlit as st

# --------- PAGE CONFIG ---------
# Set up the page configuration
st.set_page_config(page_title='Your App Title', page_icon=':shark:', layout='wide', initial_sidebar_state='expanded')

# --------- SIDEBAR TOGGLE ---------
# Floating button for sidebar toggle
sidebar_visible = st.sidebar.button('Toggle Sidebar', key='sidebar')
if sidebar_visible:
    st.sidebar.markdown('### Sidebar Content')  # Replace with actual sidebar content
else:
    st.sidebar.empty()  # Hides the sidebar if not visible

# --------- TRANSLATIONS ---------