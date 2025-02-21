import streamlit as st
import pdfplumber
import fitz  # PyMuPDF
# from sentence_transformers import SentenceTransformer
import requests
import json
import time
# pip install pdfplumber sentence-transformers firebase-admin pinecone-client  requests

st.title("IBM Granite Hackathon: Workflow Agent")
st.write("Author: Parin Acharya")

# embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def extract_text_from_pdf(file):
    start_time = time.time()  # Start timing
    text = ''
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + ' '  # Concatenate text from each page
    end_time = time.time()  # End timing
    extraction_time = end_time - start_time  # Calculate extraction time
    st.write(f'Time taken to extract text: {extraction_time:.2f} seconds')  # Display extraction time
    return text.strip()  # Return the extracted text without leading/trailing spaces

# File uploader
uploaded_file = st.file_uploader("Choose a file", type=["pdf", "txt", "png", "jpg"])

if uploaded_file is not None:
    # Display the file based on its type
    if uploaded_file.type == "application/pdf":
        st.write("Displaying PDF:")
        st.download_button("Download PDF", uploaded_file, file_name=uploaded_file.name)
        text = extract_text_from_pdf(uploaded_file)  # Extract text from the uploaded PDF
        st.success('Text received successfully!')  # Display success message for text received

    else:
        st.warning("Unsupported file type.")

    if text:
        url = 'https://us-south.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29'

        body = {
            'input': """You are an expert business workflow analyzer. Your role is to analyze a business'\''s context, analyze each step in its current workflow critically and score each step. Your tasks are as follows:

                Use the provided is the context {text}

                1. **Extract the Company Context:**  
                - Retrieve key details from the company introduction (name, size, industry, location).

                2. **Process Each Workflow Step:**  
                - For each of the 10 workflow steps, extract the detailed information including the business tools in use and any quantitative metrics provided.
                - Summarize each step into a concise 10 to 15 word sentence that captures the essence of the step.

                3. **Score Workflow Efficiency:**  
                - Evaluate and assign an efficiency score for each workflow step. Use scoring metrics similar to those employed in IBM business assessments (for example, consider factors like throughput, error rate, cycle time, and automation effectiveness).
                - The score should be a numerical value from 1 (poor efficiency) to 10 (excellent efficiency).

                4. **Output Format:** 
                - Only produce the final output in a JSON format. No other descriptions are required. Again, JSON format only.
                - Each workflow step should be represented as a JSON object with the following keys:
                    - \"step_summary\": the 10 to 15 word summary of the step.
                    - \"efficiency_score\": the numerical score assigned.
                    - \"metrics\": a brief description of the metrics or rationale used for scoring.
                - Ensure the JSON is clean and fully parsable.

                Please process the test_data accordingly and output the results in the required JSON format.

                Think through this step by step. Verify each step. Do not ever hallucinate.
                """, 
            'Output': '',
            'parameters': {
                'decoding_method': 'greedy',
                'max_new_tokens': 7999,
                'min_new_tokens': 0,
                'repetition_penalty': 1
            },
            "model_id": "ibm/granite-3-8b-instruct",
            "project_id": "f284f75e-ea6b-4395-a973-1b7b02b2c176"
        }
        
        headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Bearer eyJraWQiOiIyMDI1MDEzMDA4NDQiLCJhbGciOiJSUzI1NiJ9.eyJpYW1faWQiOiJJQk1pZC02NjgwMDBYNjFPIiwiaWQiOiJJQk1pZC02NjgwMDBYNjFPIiwicmVhbG1pZCI6IklCTWlkIiwic2Vzc2lvbl9pZCI6IkMtOTBkMWExN2MtZDQ5OS00NDBhLThiMTUtYmIwMDFmMDMzNzVmIiwic2Vzc2lvbl9leHBfbWF4IjoxNzQwMjQ3NzMxLCJzZXNzaW9uX2V4cF9uZXh0IjoxNzQwMTcwNDg0LCJqdGkiOiJmMmQ0NjhhZC0wYjAxLTQ1YTUtYmY4Zi0xNGFjNjk5MmE4MWYiLCJpZGVudGlmaWVyIjoiNjY4MDAwWDYxTyIsImdpdmVuX25hbWUiOiJQYXJpbiIsImZhbWlseV9uYW1lIjoiQWNoYXJ5YSIsIm5hbWUiOiJQYXJpbiBBY2hhcnlhIiwiZW1haWwiOiJhY2hhcnlhcGFyaW4wNUBnbWFpbC5jb20iLCJzdWIiOiJhY2hhcnlhcGFyaW4wNUBnbWFpbC5jb20iLCJhdXRobiI6eyJzdWIiOiJhY2hhcnlhcGFyaW4wNUBnbWFpbC5jb20iLCJpYW1faWQiOiJJQk1pZC02NjgwMDBYNjFPIiwibmFtZSI6IlBhcmluIEFjaGFyeWEiLCJnaXZlbl9uYW1lIjoiUGFyaW4iLCJmYW1pbHlfbmFtZSI6IkFjaGFyeWEiLCJlbWFpbCI6ImFjaGFyeWFwYXJpbjA1QGdtYWlsLmNvbSJ9LCJhY2NvdW50Ijp7InZhbGlkIjp0cnVlLCJic3MiOiI5MjI1NWJkODc1Njg0NDc5OTQ4YTM4MDRiYzM4MjgwYiIsImltc191c2VyX2lkIjoiMTMzMDU0ODYiLCJpbXMiOiIyOTcxOTkwIn0sImlhdCI6MTc0MDE2MzI4MiwiZXhwIjoxNzQwMTY0NDgyLCJpc3MiOiJodHRwczovL2lhbS5jbG91ZC5pYm0uY29tL2lkZW50aXR5IiwiZ3JhbnRfdHlwZSI6InVybjppYm06cGFyYW1zOm9hdXRoOmdyYW50LXR5cGU6cGFzc2NvZGUiLCJzY29wZSI6ImlibSBvcGVuaWQiLCJjbGllbnRfaWQiOiJieCIsImFjciI6MSwiYW1yIjpbInB3ZCJdfQ.OLWe11XtIedjO9eTBbtY1v66sefLtwBXi0C8bFhzw68u2K897F1a6ewsP6JagqADSAGHqdqmKcAHWlt3XOg4Q5xbNxSRxirDag-Ze4V-yFq6LhqQRbRNJoP1tqJDCIHWDj7Q5MpR8zrkHLjmAbPBz1yhC0NV0dGNlN_cottNRsMPjNtE4vEkFe5cFqLcn2Mupzia_QY0qm4oK4PoGlVtYhmZdVbnHsdjPN1IgN0Rak_GkrC1VP8kr6DQ_hS8Yf5V95AXTTQde01F2oTkLC4HGbRVxBR2q9rHOcCiplKI3GoViAre7ZRjfeRl0_PgNVYYUSI7nuCqAg74Ruk67WlcIw"
        }

        try:
            response = requests.post(url, headers=headers, json=body)
            if response.status_code == 200:
                st.success('Response received successfully!')  # Display success message for response
                data = response.json()  # Corrected to call the json method
                st.write('Response Data:', data)  # Display the response data for tracking
            else:
                st.error(f'Error: {response.status_code} - {response.text}')  # Display error message if response is not 200
        except Exception as e:
            st.error(f'An error occurred: {str(e)}')  # Display error message for exceptions

def extract_from_granite():
    # function to parse JSON for each step in the workflow ###










