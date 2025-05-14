import streamlit as st
from gemini_sql_agent import answer_question

st.title("LAPD Crime Data Q&A")

user_question = st.text_input("Ask a question about LAPD crime data:")
if st.button("Submit") and user_question:
    with st.spinner("Generating answer..."):
        response = answer_question(user_question)
        st.write(response)
