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

def extract_from_granite(response_data):
    try:
        # Check if 'results' is present and not empty
        if 'results' in response_data and len(response_data['results']) > 0:
            results = response_data['results'][0]['generated_text']
        else:
            st.error("No results found in the response data.")
            return  # Exit the function if no results are found
        
        # Extract the JSON output from the generated text
        json_output_start = results.find("[JSON Output]") + len("[JSON Output]\n\n")
        
        # Ensure the JSON output section exists
        if json_output_start == -1:
            st.error("JSON Output section not found in the generated text.")
            return
        
        json_output = results[json_output_start:].strip().split("\n```json\n")
        
        # Check if the JSON output is correctly formatted
        if len(json_output) < 2:
            st.error("Invalid JSON output format.")
            return
        
        json_output = json_output[1].strip().split("\n```")[0]
        
        # Load the JSON output
        workflow_steps = json.loads(json_output)
        
        # Print each step's details to the terminal
        for step in workflow_steps:
            step_summary = step['step_summary']
            efficiency_score = step['efficiency_score']
            metrics = step['metrics']
            print(f"Step Summary: {step_summary}")
            print(f"Efficiency Score: {efficiency_score}")
            print(f"Metrics: {metrics}")
            print("-" * 40)  # Separator for readability

    except json.JSONDecodeError as e:
        st.error(f"Failed to decode JSON: {str(e)}")
    except IndexError as e:
        st.error(f"Index error: {str(e)}. Check the structure of the response data.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")


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
                - Retrieve key details from the company introduction (name, size, industry, location). Do not output any response yet.

                2. **Process Each Workflow Step:**  
                - For each of the 10 workflow steps, extract the detailed information including the business tools in use and any quantitative metrics provided.
                - Summarize each step into a concise 10 to 15 word sentence that captures the essence of the step.Do not output any response yet.

                3. **Score Workflow Efficiency:**  
                - Evaluate and assign an efficiency score for each workflow step. Use scoring metrics similar to those employed in IBM business assessments (for example, consider factors like throughput, error rate, cycle time, and automation effectiveness).
                - The score should be a numerical value from 1 (poor efficiency) to 10 (excellent efficiency). Do not output any response yet.

                4. **Output Format:** - Here is the output format:
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
        "Authorization": "Bearer eyJraWQiOiIyMDI1MDEzMDA4NDQiLCJhbGciOiJSUzI1NiJ9.eyJpYW1faWQiOiJJQk1pZC02NjgwMDBYNjFPIiwiaWQiOiJJQk1pZC02NjgwMDBYNjFPIiwicmVhbG1pZCI6IklCTWlkIiwic2Vzc2lvbl9pZCI6IkMtOTBkMWExN2MtZDQ5OS00NDBhLThiMTUtYmIwMDFmMDMzNzVmIiwic2Vzc2lvbl9leHBfbWF4IjoxNzQwMjQ3NzMxLCJzZXNzaW9uX2V4cF9uZXh0IjoxNzQwMTcxODE5LCJqdGkiOiI4NmQ0ZDE2ZC1kMmIxLTQyZTMtOTk3OC00MzNhOTdiZGIzNTQiLCJpZGVudGlmaWVyIjoiNjY4MDAwWDYxTyIsImdpdmVuX25hbWUiOiJQYXJpbiIsImZhbWlseV9uYW1lIjoiQWNoYXJ5YSIsIm5hbWUiOiJQYXJpbiBBY2hhcnlhIiwiZW1haWwiOiJhY2hhcnlhcGFyaW4wNUBnbWFpbC5jb20iLCJzdWIiOiJhY2hhcnlhcGFyaW4wNUBnbWFpbC5jb20iLCJhdXRobiI6eyJzdWIiOiJhY2hhcnlhcGFyaW4wNUBnbWFpbC5jb20iLCJpYW1faWQiOiJJQk1pZC02NjgwMDBYNjFPIiwibmFtZSI6IlBhcmluIEFjaGFyeWEiLCJnaXZlbl9uYW1lIjoiUGFyaW4iLCJmYW1pbHlfbmFtZSI6IkFjaGFyeWEiLCJlbWFpbCI6ImFjaGFyeWFwYXJpbjA1QGdtYWlsLmNvbSJ9LCJhY2NvdW50Ijp7InZhbGlkIjp0cnVlLCJic3MiOiI5MjI1NWJkODc1Njg0NDc5OTQ4YTM4MDRiYzM4MjgwYiIsImltc191c2VyX2lkIjoiMTMzMDU0ODYiLCJpbXMiOiIyOTcxOTkwIn0sImlhdCI6MTc0MDE2NDYxNywiZXhwIjoxNzQwMTY1ODE3LCJpc3MiOiJodHRwczovL2lhbS5jbG91ZC5pYm0uY29tL2lkZW50aXR5IiwiZ3JhbnRfdHlwZSI6InVybjppYm06cGFyYW1zOm9hdXRoOmdyYW50LXR5cGU6cGFzc2NvZGUiLCJzY29wZSI6ImlibSBvcGVuaWQiLCJjbGllbnRfaWQiOiJieCIsImFjciI6MSwiYW1yIjpbInB3ZCJdfQ.RxkMVWrbrTHmxLPzPJL_c_WGAiYbhlc8h-qd9PFVl7B-ood2TQT_1-HT_7lkq_38Rxga-bTVElW0USqkUjtMCzckikjtn32A-21musJVgLULGvRmxHUwLaliS5fHLebi_nVoT8viEl8g5rUDCU73tlywq4KjFGPfT7b8pUdKXiWl3NPDC1xGLd4UX11hZ246xI6KnPfIVz1cFZFj899NWxiIF0dcvWa-Ye88nSQ9txHkLqCaQQgAd876cljWTBHoXKezPVw7LNVZu_Eq804ANLiffwMZj0mnxa96yQ3xXQjB4O8kD4mSbWN-56VAg4qc9I5_fZ4dBUp5uCDlypsEcw"
        }

        st.write("Making API request...")
        response = requests.post(url, headers=headers, json=body)

        if response.status_code == 200:
            st.success('Response received successfully!')  # Display success message for response
            response_data = response.json()  # Get the JSON data from the response
            st.write(response_data) # for debugging
            extract_from_granite(response_data)  # Pass the JSON data to the function
        else:
            st.error(f'Error: {response.status_code} - {response.text}')  # Display error message if response is not 200

        