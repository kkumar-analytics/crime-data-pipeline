"""
🚓 LAPD Crime Explorer: A Streamlit Application for Querying Crime Data

This application provides an intuitive interface for users to explore LAPD crime data
using natural language queries. Leveraging the power of Large Language Models (LLMs)
and Snowflake SQL, it translates user questions into SQL queries and presents the
results in a user-friendly format.
"""
import streamlit as st
from sql_agent import answer_question

# Set page config for better presentation in a browser tab
st.set_page_config(page_title="LAPD Crime Explorer", page_icon="🚓", layout="centered")

# Custom CSS to enhance the visual appeal and user experience
st.markdown("""
    <style>
    /* Larger and more readable main font */
    .big-font {
        font-size: 24px !important;
        font-weight: bold;
        color: #2c3e50; /* Darker, professional color */
    }
    /* Improved button styling */
    .stButton>button {
        background-color: #3498db; /* Brighter, more engaging blue */
        color: white;
        border-radius: 12px; /* More rounded corners */
        padding: 0.75em 1.5em; /* Slightly larger padding */
        font-size: 18px; /* Larger font for better readability */
        border: none; /* Remove default border */
        box-shadow: 0 2px 5px rgba(0,0,0,0.15); /* Subtle shadow for depth */
        transition: background-color 0.3s ease; /* Smooth hover effect */
    }
    .stButton>button:hover {
        background-color: #2980b9; /* Darker shade on hover */
    }
    /* Enhanced text input styling */
    .stTextInput>div>div>input {
        border-radius: 12px;
        padding: 12px;
        border: 1px solid #bdc3c7; /* Light gray border */
        font-size: 16px;
    }
    .stTextInput>div>div>input:focus {
        border-color: #3498db; /* Highlight on focus */
        box-shadow: 0 0 5px rgba(52, 152, 219, 0.5); /* Focus shadow */
    }
    /* More prominent markdown text */
    .stMarkdown {
        font-size: 18px;
        line-height: 1.6; /* Improved line spacing for readability */
    }
    /* Center the main title */
    .title-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 15px;
    }
    .police-icon {
        font-size: 2em;
        margin-right: 10px;
        color: #e74c3c; /* A more noticeable color for the icon */
    }
    /* Subtitle styling */
    .subtitle {
        font-size: 16px;
        color: #7f8c8d; /* Muted color for subtitle */
        text-align: center;
        margin-bottom: 20px;
    }
    /* Success message styling */
    .stSuccess {
        color: #27ae60; /* Green for success */
        font-weight: bold;
        margin-top: 10px;
    }
    /* Spinner styling */
    .stSpinner > div > div > div {
        border-top-color: #3498db !important; /* Match spinner color to button */
    }
    </style>
""", unsafe_allow_html=True)


st.markdown("<div class='title-container'><span class='police-icon'>🚓</span><h1 class='big-font'>LAPD Crime Explorer</h1></div>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Ask natural language questions about LAPD crime data. Powered by LLM + Snowflake SQL.</p>", unsafe_allow_html=True)
user_question = st.text_input("🔍 Enter your crime-related question:", placeholder="e.g., What are the safest neighborhoods in the last month?")

if st.button("Submit"):
    if user_question:
        with st.spinner("🤖 Processing your query..."):
            try:
                response = answer_question(user_question)
                st.success("✅ Query results:")
                st.markdown(response)
            except Exception as e:
                st.error(f"⚠️ An error occurred: {e}")
                st.info("Please ensure your question is clear and the database connection is working correctly.")
    else:
        st.warning("Please enter a question to explore the crime data.")