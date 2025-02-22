# utils.py
import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()
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

###############################################################################################
# ReAct Agent V2

params = {
    "space_id": "825b15ec-b09f-413c-80ed-4e7fd3fc0bb0"
}

class WorkflowAnalyzer:
    def __init__(self):
        self.workflow_response = None
    
    def set_workflow_response(self, response):
        self.workflow_response = response
    
    def get_workflow_response(self):
        return self.workflow_response

# Create a global instance
workflow_analyzer = WorkflowAnalyzer()

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
        response_data = workflow_analyzer.get_workflow_response()
        if not response_data:
            print("Warning: No workflow response data available")
            response_data = {}

        payload = context.get_json()
        messages = convert_messages(payload.get("messages", []))
        
        model_instance = create_chat_model(client)
        tools = create_tools()
        
        # Initialize agent workers
        summarizer = create_agent(model_instance, create_tools(), f"""From the context provided: {response_data}
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
            - The JSON object output should have the following keys:
                    - \"step_summary\": the brief 10 to 15 word summary of each business workflow step with the step number in chronological order.
                    - \"efficiency_score\": the numerical score assigned out of 10 for each business workflow step.
                    - \"explanation\": a description of specific steps to improve workflow efficiency and an estimated improvement in affected metrics for each business workflow step.        
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
                            "content": "REMINDER: Final output must be JSON array with: step_summary, efficiency_score, improvements and expected_impact for EACH business workflow step."
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

if __name__ == "__main__":
    messages = [
        {"role": "system", "content": "You are an expert multi-agent framework that analyzes of a business workflow. Maintain JSON format throughout the output of the analysis chain and present in a clean, parsable format."},
        {"role": "user", "content": "Begin the business workflow analysis chain."}
    ]
    context = RealContext(messages)
    generate, _ = gen_ai_service(context)
    response = generate(context)
    print(json.dumps(response, indent=2))