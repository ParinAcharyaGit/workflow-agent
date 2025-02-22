import streamlit as st
import pdfplumber
import fitz  # PyMuPDF
# from sentence_transformers import SentenceTransformer
import requests
import os
from dotenv import load_dotenv
import json
import time
from streamlit_flow import streamlit_flow
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge
from streamlit_flow.state import StreamlitFlowState
# pip install pdfplumber sentence-transformers firebase-admin pinecone-client  requests

load_dotenv()

st.title("IBM Granite Hackathon: Workflow Agent")
st.write("Author: Parin Acharya")

# embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    # Authentication token for IBM Watson
API_KEY = os.environ['IBM_API_KEY']
NEW_API_KEY = os.environ['NEW_API_KEY']
token_response = requests.post('https://iam.cloud.ibm.com/identity/token', data={"apikey":
API_KEY, "grant_type": 'urn:ibm:params:oauth:grant-type:apikey'})
mltoken = token_response.json()["access_token"]

def generate_iam_token(NEW_API_KEY):
    url = 'https://iam.cloud.ibm.com/identity/token'
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": NEW_API_KEY
    }

    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json().get("access_token")
    
access_token = generate_iam_token(NEW_API_KEY)

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
    workflow_steps = []  # Initialize workflow_steps to avoid UnboundLocalError
    try:
        # Access the results
        results = response_data['results'][0]['generated_text']
        
        # Extract the JSON output from the generated text
        json_output_start = results.find("[")  # Find the start of the JSON array
        json_output = results[json_output_start:].strip()  # Get the JSON part
        
        # Load the JSON output
        workflow_steps = json.loads(json_output)  # Parse the JSON
        
        # Print each step's details to the terminal
        for step in workflow_steps:
            step_summary = step['step_summary']
            efficiency_score = step['efficiency_score']
            explanation = step['explanation']
            print(f"Step Summary: {step_summary}")
            print(f"Efficiency Score: {efficiency_score}")
            print(f"Explanation: {explanation}")
            print("-" * 40)  # Separator for readability

    except json.JSONDecodeError as e:
        st.error(f"Failed to decode JSON: {str(e)}")
    except IndexError as e:
        st.error(f"Index error: {str(e)} - Check the structure of the response data.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

    if workflow_steps:  # Only proceed if workflow_steps is not empty
        st.write("Generating flow diagram... hang on tight...")

        # Create nodes for each workflow step
        nodes = []
        for i, step in enumerate(workflow_steps):
            step_summary = step['step_summary']
            efficiency_score = step['efficiency_score']
            explanation = step['explanation']
            
            # Determine the background color based on the efficiency score
            if efficiency_score < 4:
                background_color = '#ff4d4d'  # Red
            elif efficiency_score < 7:
                background_color = '#ffcc00'  # Orange
            else:
                background_color = '#00c04b'  # Green

            content = f'Step: {step_summary}\nScore: {efficiency_score}\nExplanation: {explanation}'
            
            node = StreamlitFlowNode(
                id=str(i + 1),  # Node ID starts from 1
                pos=(100 + i * 300, 100),  # Increase spacing between nodes
                data={'content': content},
                node_type='default',  # Change as needed
                source_position='right',
                target_position='left',
                draggable=False,
                style={'color': 'white', 'backgroundColor': background_color, 'border': '2px solid white', 'width': '200px'}  # Set background color
            )
            nodes.append(node)

        # Create edges for the flow in a linear fashion
        edges = []
        for i in range(len(workflow_steps) - 1):
            edges.append(StreamlitFlowEdge(
                id=f'{i+1}-{i+2}', 
                source=str(i + 1), 
                target=str(i + 2), 
                animated=True, 
                marker_end={'type': 'arrow'}
            ))

        # Create the flow state
        state = StreamlitFlowState(nodes, edges)

        # Render the flow visualization
        streamlit_flow('static_flow',
                       state,
                       fit_view=True,
                       show_minimap=False,
                       show_controls=False,
                       pan_on_drag=True,
                       allow_zoom=True)  # Allow zooming for better visibility
    else:
        st.error("No workflow steps found. Please check the response data.")

# Starting point
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
            'input': f"""You are an expert business workflow analyzer. Your role is to analyze a business'\''s context, analyze each step in its current workflow critically and score each step. Your tasks are as follows:

                Use only the provided context: {text}

                1. **Extract the Company Context:**  
                - Retrieve key details from the company introduction (name, size, industry, location). Do not output any response yet.

                2. **Process Each Workflow Step:**  
                - For each of the 10 workflow steps, extract the detailed information including the business tools in use and any quantitative metrics provided.
                - Summarize each step into a concise 10 to 15 word sentence that captures the essence of the step.Do not output any response yet.

                3. **Score Workflow Efficiency:**  
                - Evaluate and assign an efficiency score for each workflow step. Use scoring metrics similar to those employed in IBM business assessments (for example, consider factors like throughput, error rate, cycle time, and automation effectiveness).
                - The score should be a numerical value from 1 (poor efficiency) to 10 (excellent efficiency). Be as critical as possible, do not just award > 6 without justification since there is always room for improvement in the current step! Do not output any response yet.

                4. **Output Format:** - Here is the output format:
                - Only produce the final output in a JSON array only, not a dictionary named 'workflow_steps' or anything like 'JSON Output:' or [JSON_OUTPUT]! Verify that none of that is mentioned. No other descriptions are required. 
                - Each JSON object should have the following keys:
                    - \"step_summary\": the 10 to 15 word summary of the step.
                    - \"efficiency_score\": the numerical score assigned.
                    - \"explanation\": a brief description of measurable, specific steps to improve workflow efficiency in this step.
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
        
        # move the bearer token to .env or add mltoken from above: Check access rights
        headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
        }

        st.write("Making API request...")
        response = requests.post(url, headers=headers, json=body)

        if response.status_code == 200:
            st.success('Response received successfully!')  # Display success message for response
            response_data = response.json()  # Get the JSON data from the response
            st.write(response_data) # for debugging
            st.write("generating visualizations...hang on tight...")
            extract_from_granite(response_data)  # Parse JSON to create flowchart
            # generate_vizualizations(response_data)  # Generate flow diagram

            # Make sidepanel available?
            st.title("WorkWise AI chat interface")
            st.session_state.clear()

            # Clear session state on initial load
            if 'page_refreshed' not in st.session_state:
                st.session_state.clear()  # Clears session on initial load
                st.session_state.page_refreshed = True

            if "messages" not in st.session_state:
                st.session_state.messages = []  # Initialize chat history

            # Turn-taking logic
            if 'waiting_for_user' not in st.session_state:
                st.session_state.waiting_for_user = False

            # Ensure we have a session key for user_input?

            # Display all messages in the history
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message['content'])

            API_KEY = os.getenv('IBM_API_KEY')
            headers = {
                'Authorization': f'Bearer + {mltoken}',
                'Content-Type': 'application/json',
            }

            input = st.text_input("Ask WorkWiseAI ...")
            # Add button to control the chat flow
            send_button = st.button('send')

            # input = st.text_input("Ask WorkWiseAI ...", key="user_input")

            if send_button:
                print('user message received')
                st.chat_message("user").markdown(input)
                st.session_state.messages.append({"role": "user", "content": f'{input}'})
                st.session_state.user_input = "" # Clear input after sending, preparing for follow-up

                if not st.session_state.waiting_for_user:
                    st.session_state.waiting_for_user = True

                    with st.spinner("Thinking..."):
                        payload_scoring = {
                            "messages": st.session_state.messages
                        }

                        response_scoring = requests.post(
                            'https://us-south.ml.cloud.ibm.com/ml/v4/deployments/528030d4-dac7-48b5-b39f-3776f6bb4ecc/ai_service?version=2021-05-01',
                            json=payload_scoring,
                            headers={'Authorization': 'Bearer ' + mltoken}
                        )

                        try:
                            response_data = response_scoring.json()
                            assistant_reply = response_data['choices'][0]['message']['content']
                        except Exception as e:
                            assistant_reply = f"Error: {str(e)}"
                        finally:
                            st.chat_message("assistant").markdown(assistant_reply)
                            st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

                    # Unlock for next message and clear input so it won't resend
                    st.session_state.waiting_for_user = False
                    # st.session_state["user_input"] = ""  # Clear input to prevent duplication on rerun
                follow_up = st.button('follow-up')
                if follow_up:
                    st.rerun()
            
        else:
            st.error(f'Error: {response.status_code} - {response.text}')  # Display error message if response is not 200

        

