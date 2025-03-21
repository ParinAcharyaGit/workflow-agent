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
import pandas as pd
import altair as alt

# pip install pdfplumber sentence-transformers firebase-admin pinecone-client  requests

load_dotenv()

st.title("IBM Granite Hackathon: WorkWiseAI")
st.write('Built on IBM’s open source granite-3.1-8b-instruct powered by IBM AgentLab, WorkWiseAI provides businesses with deep workflow insights, data-driven efficiency scoring, and AI-generated optimization strategies.')
st.markdown("Solution by: [Parin Acharya](https://www.linkedin.com/in/parinacharya)")
st.markdown("View [GitHub repository](https://www.github.com/ParinAcharyaGit/workflow-agent)")

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
        st.write("Generating flow diagram...")

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

if 'tab1_completed' not in st.session_state:
    st.session_state.tab1_completed = False

# fix on-load error
if 'required_response' not in st.session_state:
    st.session_state.required_response = None

with tab1:
    st.image("./images/workwiseai_cover_image.jpg")
        # Display a welcome message and guide
    # Provide a brief overview of the features
    st.header('Problem statement')
    st.write('Large modern businesses and fast-growing startups often struggle with operational inefficiencies hidden within their workflows. Traditional process audits can be time-consuming, subjective, and costly. WorkwiseAI automates this process, delivering real-time, AI-driven workflow analysis that enhances decision-making.')

    with st.expander('Real-World Use Cases of Business Workflow Analysis using IBM Products'):
        st.markdown("""
        1. Vodafone, a global communications leader, is using IBM Watson to simulate and analyze digital disucssions with its AI powered virtual agent, reducing testing timelines to under 1 minute. [Read more](https://www.ibm.com/case-studies/vodafone-tobi)
        2. Artefact, a leading French Bank uses a portfolio of personas represented by AI identities, allowing professionals to reveal crucial insights from customer behavior. [Read more](https://www.ibm.com/case-studies/artefact)
        """)

    with st.expander('Market scope, revenue streams and scalability'):
        st.markdown("""
        1. TOTAL ADDRESSABLE MARKET: The Business Process Automation (BPA) market is projected to reach US$ 19.6 billion by 2026. WorkWiseAI targets sectors such as finance, healthcare, cloud computing and manufacturing.
        2. REVENUE STREAMS: WorkWiseAI could attract revenue streams from SAAS licensing, enterprise consulting services and OEM partnership deals.
        3. MARKET COMPETITORS: Platforms like Blue Prism and Microsoft Power Automate offer limited AI-driven insights and contextual analysis of existing and new business workflows WorkWiseAI offers a Unique Selling Proposition through a custom S3 Agent workflow analysis pipeline. SEE AGENT TAB.
        4. SCALABILITY: Platforms like IBM BPM offer reliable enterprise integration and scalability. WorkWiseAI could benefit from vertical expansion to industry-specific needs and further integration of IBM Watson Discovery and Orchestrate.
    """)

    with st.expander("Getting Started with WorkWise AI"):
        st.markdown("""
        To explore the features of WorkWiseAI, follow these steps:

        1. **Upload Your Business Process Document (BPD)**: Start by uploading a PDF or text document in the **Home** tab.

        2. **Visualizations**: View workflow visualizations generated from your document.

        3. **Chat Interface**: Interact with WorkWise AI for insights and recommendations.

        4. **S3 Agent Tab**: Explore advanced analysis features powered by the WorkWise S3 Agent.

        5. **Review Past Analyses**: Compare efficiency scores from past analyses, if available, in the agent tab.

        Feel free to explore each tab and make the most of the tools provided!
        """)

    # Add an image to make the interface more engaging
    # Assuming the image is located in the same directory as your main.py file


# File uploader
    uploaded_file = st.file_uploader("Upload Business Process Document (BPD)", type=["pdf", "txt", "png", "jpg"])

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
            "Authorization": f"Bearer {access_token}"
            }

            st.write("Making API request...")
            response = requests.post(url, headers=headers, json=body)

            if response.status_code == 200:
                st.success('Response received successfully!')  # Display success message for response
                response_data = response.json()  # Get the JSON data from the response
                
                                
                # set_response(response_data) # for use in utils.py

                st.write("Generated Visualizations")
                extract_from_granite(response_data)  # Parse JSON to create flowchart
                # generate_vizualizations(response_data)  

                # Make sidepanel available?
                st.title("WorkWiseAI chat interface")
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

                input = st.text_area("Ask WorkWiseAI ...", height = 150)
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
                st.error(f'Error: {response.status_code} - {response.text}') 
            
     # Display error message if response is not 200
            st.session_state.tab1_completed = True
            st.session_state.required_response = response_data
    # load context for tab 2
    # parsed_context = response_data

with tab2:
    st.image("./images/workflow.png", caption='Architecture Overview')
    st.write('Upload Business Process Document in the Home tab to get started with S3 Agent Analysis')
    if st.session_state.tab1_completed:
        # Waits for tab 1 session to complete before accessing global variables.
        # prevents on_load errors

        required_data = st.session_state.required_response    
        
        with st.spinner('Hang on tight for a response from the WorkWise S3 Agent.'):
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
                    summarizer = create_agent(model_instance, create_tools(), f"""From the context provided: {required_data}
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
            # Display the parsed data on Streamlit UI
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
                    # with st.expander(f"{step['step_summary']} (Score: {step['efficiency_score']})"):
                    #     st.markdown(f"**Explanation:** {step['explanation']}")

            except json.JSONDecodeError as e:
                st.error(f"Failed to decode JSON: {str(e)}")
            except IndexError as e:
                st.error(f"Index error: {str(e)} - Check the structure of the response data.")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

                # Function to display steps in Streamlit
            def display_steps(parsed_responses):
                for item in parsed_responses:
                    if 'steps' in item:
                        for idx, step in enumerate(item['steps']):
                            # Get corresponding legacy step if exists
                            legacy_step = analyzed_steps[idx] if idx < len(analyzed_steps) else None
                            
                            # Create comparison title
                            title = f"{step.get('step_summary', 'Step')} "
                            title += f"(New Score: {step.get('efficiency_score', 'N/A')}"
                            if legacy_step:
                                title += f" vs Legacy: {legacy_step.get('efficiency_score', 'N/A')})"
                            else:
                                title += ")"
                            
                            # Create expander with comparison
                            with st.expander(f"Step {idx+1}: {step.get('step_summary', 'Step')}"):
                                # Create two columns for layout
                                col1, col2 = st.columns(2)
                                
                                # Legacy Analysis (Left-aligned)
                                with col1:
                                    if legacy_step:
                                        st.markdown(
                                            f"<div style='text-align: left; color: #ffd700;'>"
                                            f"<strong>🡐 Previous Score: {legacy_step.get('efficiency_score', 'N/A')}</strong><br>"
                                            f"{legacy_step.get('explanation', 'No legacy explanation available')}"
                                            f"</div>", 
                                            unsafe_allow_html=True
                                        )
                                
                                # New Analysis (Right-aligned)
                                with col2:
                                    st.markdown(
                                        f"<div style='text-align: right; color: #00ff00;'>"
                                        f"<strong>New Score: {step.get('efficiency_score', 'N/A')} 🡒</strong><br>"
                                        f"{step.get('explanation', 'No explanation available')}"
                                        f"</div>", 
                                        unsafe_allow_html=True
                                    )
                                
                                
                                
                                # Add improvement recommendations if available
                                # if 'improvements' in step:
                                #     st.markdown("**Recommendations:**")
                                #     for improvement in step['improvements']:
                                #         st.markdown(f"- {improvement}")
                    else:
                        st.warning("No steps found in response.")

            # Parse the responses
        parsed_responses = parse_responses(agent_response)

        display_steps(parsed_responses)

            
        if parsed_responses and 'steps' in parsed_responses[0]:
        # Extract step numbers and efficiency scores
            steps = [f"Step {i+1}" for i in range(len(parsed_responses[0]['steps']))]
            agent_scores = [step['efficiency_score'] for step in parsed_responses[0]['steps']]
            legacy_scores = [step['efficiency_score'] for step in analyzed_steps] if analyzed_steps else [0] * len(agent_scores)

            # Create a DataFrame for the chart
            data = pd.DataFrame({
                'Step': steps,
                'Legacy Workflow': legacy_scores,
                'Agent Workflow': agent_scores
            })

            # Melt the DataFrame to have a long-form format suitable for Altair
            data_melted = data.melt('Step', var_name='Workflow', value_name='Efficiency Score')

            # Create the Altair chart
            chart = alt.Chart(data_melted).mark_bar().encode(
                x=alt.X('Step:N', title='Workflow Step'),
                y=alt.Y('Efficiency Score:Q', title='Efficiency Score'),
                color=alt.Color('Workflow:N', scale=alt.Scale(range=['#00ff00','#ffd700'])),
                tooltip=['Step', 'Workflow', 'Efficiency Score']
            ).properties(
                title='Comparison of Efficiency Scores',
                width=600,
                height=400
            )

            # Display the chart in Streamlit
            st.altair_chart(chart, use_container_width=True)
        else:
            st.error("No data available to display the chart.")
