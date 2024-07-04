import streamlit as st
from workflow import process_question

def main():
    st.title("RetailX AI Assistant")
    st.write("Ask a question about RetailX customers, products, and sales:")

    question = st.text_input("Question")
    if st.button("Submit"):
        if question:
            try:
                answer = process_question(question)
                st.write("Answer:", answer)
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
        else:
            st.write("Please enter a question.")

if __name__ == "__main__":
    main()