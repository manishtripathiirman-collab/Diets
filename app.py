import streamlit as st

st.title("My Online Streamlit App")
st.write("Hello! This app is running completely free from GitHub and Streamlit Cloud.")

name = st.text_input("What is your name?")
if name:
    st.success(f"Welcome, {name}!")
