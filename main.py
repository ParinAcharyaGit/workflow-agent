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

from shared_state import init_state, set_response

# pip install pdfplumber sentence-transformers firebase-admin pinecone-client  requests

load_dotenv()

st.title("IBM Granite Hackathon: Workflow Agent")
st.write("Author: Parin Acharya")

# embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Authentication token for IBM Watson
API_KEY = os.environ['IBM_API_KEY']
token_response = requests.post('https://iam.cloud.ibm.com/identity/token', data={"apikey":
API_KEY, "grant_type": 'urn:ibm:params:oauth:grant-type:apikey'})
mltoken = token_response.json()["access_token"]

def generate_iam_token():
    # Retrieve and trim the API key from the environment variable.
    NEW_API_KEY = os.environ.get('NEW_API_KEY')

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
        token = response.json().get("access_token")
        if token:
            return token
        else:
            print("Access token not found in response!")
            return None
    else:
        print('Error with IAM token:', response.text)
        return None

access_token = generate_iam_token()
print(access_token)

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
        json_output = results.replace("[JSON Output]", "").strip()  # Remove the [JSON Output] marker
        json_output = json_output[json_output.find("["):].strip()  # Find the actual array start
        
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
# function ends here

# Starting point
tab1, tab2 = st.tabs(['Home', 'Agent'])

with tab1:
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
                        - \"explanation\": a description of the main factor(s) leading to workflow inefficiency, with associated metrics, in this step.
                    - Ensure the JSON is clean and fully parsable.

                    Please process the test_data accordingly and output the results in the required JSON format.

                    Think through this step by step. Verify each step. Do not ever hallucinate.
                    """, 
                'Output': '',
                'parameters': {
                    'decoding_method': 'greedy',
                    'max_new_tokens': 2000,
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
            "Authorization": f"Bearer eyJraWQiOiIyMDI1MDEzMDA4NDQiLCJhbGciOiJSUzI1NiJ9.eyJpYW1faWQiOiJJQk1pZC02NjgwMDBYNjFPIiwiaWQiOiJJQk1pZC02NjgwMDBYNjFPIiwicmVhbG1pZCI6IklCTWlkIiwic2Vzc2lvbl9pZCI6IkMtOGFlMTBkYmItYjhmZS00ZmE0LThlZWMtMThiYWZmNmQwOWJhIiwic2Vzc2lvbl9leHBfbWF4IjoxNzQwMzQ3MzM5LCJzZXNzaW9uX2V4cF9uZXh0IjoxNzQwMjc5MjYyLCJqdGkiOiI1MTE0Y2JiMC1iNzc5LTQyN2QtODFkMS02ZWRiYjY4ZWE2MmMiLCJpZGVudGlmaWVyIjoiNjY4MDAwWDYxTyIsImdpdmVuX25hbWUiOiJQYXJpbiIsImZhbWlseV9uYW1lIjoiQWNoYXJ5YSIsIm5hbWUiOiJQYXJpbiBBY2hhcnlhIiwiZW1haWwiOiJhY2hhcnlhcGFyaW4wNUBnbWFpbC5jb20iLCJzdWIiOiJhY2hhcnlhcGFyaW4wNUBnbWFpbC5jb20iLCJhdXRobiI6eyJzdWIiOiJhY2hhcnlhcGFyaW4wNUBnbWFpbC5jb20iLCJpYW1faWQiOiJJQk1pZC02NjgwMDBYNjFPIiwibmFtZSI6IlBhcmluIEFjaGFyeWEiLCJnaXZlbl9uYW1lIjoiUGFyaW4iLCJmYW1pbHlfbmFtZSI6IkFjaGFyeWEiLCJlbWFpbCI6ImFjaGFyeWFwYXJpbjA1QGdtYWlsLmNvbSJ9LCJhY2NvdW50Ijp7InZhbGlkIjp0cnVlLCJic3MiOiI5MjI1NWJkODc1Njg0NDc5OTQ4YTM4MDRiYzM4MjgwYiIsImltc191c2VyX2lkIjoiMTMzMDU0ODYiLCJpbXMiOiIyOTcxOTkwIn0sImlhdCI6MTc0MDI3MjA1OSwiZXhwIjoxNzQwMjczMjU5LCJpc3MiOiJodHRwczovL2lhbS5jbG91ZC5pYm0uY29tL2lkZW50aXR5IiwiZ3JhbnRfdHlwZSI6InVybjppYm06cGFyYW1zOm9hdXRoOmdyYW50LXR5cGU6cGFzc2NvZGUiLCJzY29wZSI6ImlibSBvcGVuaWQiLCJjbGllbnRfaWQiOiJieCIsImFjciI6MSwiYW1yIjpbInB3ZCJdfQ.EyrdIfNuPhzM-2SPAwWCv34cKvAWa3g3XJRyUB14BfhuhbqnXIzKqKI4kNiAPc3rr8Yrr2Qr1e9rLX0LbjExx0_QeuvPPH2UAKNt0BU0d2kIJsS3EXP70b3bt8UHa2_0lukLUzsDS0RlLnOfYjwhZXCrTSY0C2hR9VxQUfq5VtHf3nRSUgNQPqqRc0LJ2csNLxRau3g636TlWNkmG4Ywg20oq7aSXLrexjMSyewnuUcyVh0558d_qKkuxUTHvFCHuF0IghSUAsKg54mfJIe_fwIUpCG_lU3dHUN3PiKOTdoWSdVydyKkxflSJbIOqgYzojGImRcEdZ3vcOddZLFE2g"
            }

            st.write("Making API request...")
            response = requests.post(url, headers=headers, json=body)

            if response.status_code == 200:
                st.success('Response received successfully!')  # Display success message for response
                response_data = response.json()  # Get the JSON data from the response
                st.write(response_data) # for debugging

                
                # set_response(response_data) # for use in utils.py

                st.write("generating visualizations...hang on tight...")
                extract_from_granite(response_data)  # Parse JSON to create flowchart
                # generate_vizualizations(response_data)  

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
                                final_data = response_scoring.json()

                                assistant_reply = final_data['choices'][0]['message']['content']
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

with tab2:
    if response_data: parsed_context = response_data
    st.write('This where the Granite Agent is instantiated.')
    IBM_API_KEY = os.getenv('IBM_API_KEY')
    url = "https://iam.cloud.ibm.com/identity/token"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": IBM_API_KEY
    }

    response = requests.post(url, headers=headers, data=data)
    watsonx_token = response.json().get("access_token")
    if watsonx_token: print("token created successfully")

    params = {
    "space_id": "825b15ec-b09f-413c-80ed-4e7fd3fc0bb0"
    }

    def gen_ai_service(context, params=params, **custom):
        from langchain_ibm import ChatWatsonx
        from ibm_watsonx_ai import APIClient
        from langchain_core.messages import AIMessage, HumanMessage
        from langchain_community.tools import WikipediaQueryRun, DuckDuckGoSearchRun
        from langchain_community.utilities import WikipediaAPIWrapper
        from langgraph.checkpoint.memory import MemorySaver
        from langgraph.prebuilt import create_react_agent

        model = "meta-llama/llama-3-3-70b-instruct"
        service_url = "https://us-south.ml.cloud.ibm.com"

        credentials = {
            "url": service_url,
            "token": context.generate_token()
        }

        client = APIClient(credentials)
        space_id = params.get("space_id")
        client.set.default_space(space_id)

        def create_chat_model(watsonx_client):
            parameters = {
                "frequency_penalty": 0,
                "max_tokens": 7500,
                "presence_penalty": 0,
                "temperature": 0,
                "top_p": 1
            }
            return ChatWatsonx(
                model_id=model,
                url=service_url,
                space_id=space_id,
                params=parameters,
                watsonx_client=watsonx_client,
            )

        def create_tools():
            from langchain_community.utilities import WikipediaAPIWrapper
            tools = []
            tools.append(WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper(top_k_results=2)))
            tools.append(DuckDuckGoSearchRun(name='business_metrics_search'))
            return tools

        def create_agent(model, tools, role_instructions):
            memory = MemorySaver()
            return create_react_agent(model, tools=tools, checkpointer=memory, state_modifier=role_instructions)

        def convert_messages(messages):
            return [
                HumanMessage(content=msg["content"]) if msg["role"] == "user" 
                else AIMessage(content=msg["content"])
                for msg in messages
            ]

        def generate(context):
            # Get workflow response from the analyzer instance

            payload = context.get_json()
            messages = convert_messages(payload.get("messages", []))
            
            model_instance = create_chat_model(client)
            tools = create_tools()
            
            # Initialize agent workers
            summarizer = create_agent(model_instance, create_tools(), f"""From the context provided: {parsed_context}
            - Identify, Analyze and number each business workflow step. Never combine steps.
            - Highlight inefficiency factors.
            - Summarize each business workflow step in 10-15 words.
            - Output format:
                {{
                    "steps": [
                        {{
                            "step_number": 1,
                            "summary": "10-15 word description",
                            "inefficiencies": ["list"]
                        }}
                    ]
                }}
            """)
            
            scorer = create_agent(model_instance, [DuckDuckGoSearchRun()], 'Score EACH business workflow step separately from 1 to 10, where 10 indicates highest efficiency, using named industry metrics. Be as critical as possible, do not just score highly without justification. Mention the metric used.')

            suggester = create_agent(model_instance, tools, """ Your role is to suggest improvements for each step. Do not use any tools in this step, your output should be JSON only.
                     
            """)

            # Chaining the agents together through carried context
            try:
                summary_result = summarizer.invoke(
                    {'messages': messages},
                    {'configurable':{'thread_id': 42 }, 'recursion_limit': 300 }
                )

                scored_result = scorer.invoke(
                    {'messages': summary_result['messages']},
                    {'configurable':{'thread_id': 42 }, 'recursion_limit': 300 }
                )

                suggestions = suggester.invoke(
                    {
                        'messages': [
                            *summary_result['messages'],
                            *scored_result['messages'],
                            {
                                "role": "user",
                                "content": """REMINDER: Final output must be JSON array with: step_summary, efficiency_score, improvements and expected_impact for EACH business workflow step.
                                    - The JSON object output must have the following keys. DO THIS FOR EACH OF THE BUSINESS WORKFLOW STEPS, YOU MUST INCLUDE ALL STEPS AND THEIR KEYS IN THE OUTPUT!!!:
                                        - "step_summary": the brief 10 to 15 word summary of each business workflow step with the step number in chronological order.
                                        - "explanation": an insightful 30 word description of specific steps to improve workflow efficiency. Include specific tools/methodologies that could be used for instance. Include which affected metrics would improve, and by what extent for each business workflow step.  
                                        - "efficiency_score": an updated numerical score as an estimate out of 10 that estimates the workflow efficiency after possible implementation of specific steps/tools/methodologies to improve workflow efficiency in this step. 
                                """
                            }
                        ]
                    }, 
                    {'configurable':{'thread_id': 42 }, 'recursion_limit': 300, 'timeout': 1200 }
                )

                try:
                    output_data = json.loads(suggestions["messages"][-1].content)
                    if not isinstance(output_data, list):
                        output_data = [output_data]
                except:
                    output_data = []

                return {
                    "headers": {"Content-Type": "application/json"},
                    "body": {
                        "choices": [{
                            "message": {
                                "role": "assistant",
                                "content": json.dumps(output_data)
                            }
                        }]
                    }
                }
            except Exception as e:
                print(f"Error in generate function: {str(e)}")
                return {
                    "headers": {"Content-Type": "application/json"},
                    "body": {
                        "choices": [{
                            "message": {
                                "role": "assistant",
                                "content": json.dumps([{"error": str(e)}])
                            }
                        }]
                    }
                }

        return generate, None

    class RealContext:
        def __init__(self, messages):
            self._messages = messages
            self._token = watsonx_token
            if not self._token:
                raise Exception("WATSONX_TOKEN environment variable not set.")

        def generate_token(self):
            return self._token

        def get_token(self):
            return self.generate_token()

        def get_json(self):
            return {"messages": self._messages}


    messages = [
        {"role": "system", "content": "You are an expert multi-agent framework that analyzes of a business workflow. Maintain JSON format throughout the output of the analysis chain and present in a clean, parsable format."},
        {"role": "user", "content": "Begin the business workflow analysis chain."}
    ]

    context = RealContext(messages)
    generate, _ = gen_ai_service(context)
    agent_response = generate(context)             # this will be used to populate the AI
    print(json.dumps(agent_response, indent=2))
    st.write(json.dumps(agent_response, indent=2))

    # Function to properly extract and parse JSON objects from concatenated responses
    st.json(agent_response)  # Displays response in Streamlit UI for debugging

    # Function to parse JSON response
    def parse_responses(raw_response):
        try:
            # Ensure response is a dictionary
            if not isinstance(raw_response, dict):
                raw_response = json.loads(raw_response)  # Convert string to dictionary if needed

            # Extract message content (which is a JSON string)
            content_str = raw_response.get('body', {}).get('choices', [{}])[0].get('message', {}).get('content', '[]')

            # Convert content string into a Python object (a list)
            parsed_data = json.loads(content_str)

            return parsed_data  # This is now a properly structured list of steps

        except json.JSONDecodeError as e:
            st.error(f"Failed to parse JSON response: {str(e)}")
            return []

    # Function to display steps in Streamlit
    def display_steps(parsed_responses):
        for item in parsed_responses:
            if 'steps' in item:  # Ensure steps exist
                for step in item['steps']:
                    # Create an expander for each step
                    with st.expander(f"{step.get('step_summary', 'Step')} (Score: {step.get('efficiency_score', 'N/A')})"):
                        st.markdown(f"**Explanation:** {step.get('explanation', 'No explanation available')}")
            else:
                st.warning("No steps found in response.")

    # Parse the responses
    parsed_responses = parse_responses(agent_response)

    # Display the parsed data on Streamlit UI
    display_steps(parsed_responses)

    # print(response_data)
    st.header('Comparison against legacy workflow') # Add thinking animation?    
    # THIS IS FOR THE LEGACY WORKFLOW
    analyzed_steps = []  # Initialize workflow_steps to avoid UnboundLocalError
    try:
        # Access the results
        analyzed_results = response_data['results'][0]['generated_text']
        
        # Extract the JSON output from the generated text
        json_output = analyzed_results.replace("[JSON Output]", "").strip()  # Remove the [JSON Output] marker
        json_output = json_output[json_output.find("["):].strip()  # Find the actual array start
        
        # Load the JSON output
        analyzed_steps = json.loads(json_output)  # Parse the JSON
        
        # Print each step's details to the terminal
        for step in analyzed_steps:
            step_summary = step['step_summary']
            efficiency_score = step['efficiency_score']
            explanation = step['explanation']
            with st.expander(f"{step['step_summary']} (Score: {step['efficiency_score']})"):
                st.markdown(f"**Explanation:** {step['explanation']}")

    except json.JSONDecodeError as e:
        st.error(f"Failed to decode JSON: {str(e)}")
    except IndexError as e:
        st.error(f"Index error: {str(e)} - Check the structure of the response data.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

