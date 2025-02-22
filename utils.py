# Helper functions for react-agent.py
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
print("Watsonx Token:", watsonx_token)
if watsonx_token: print("token created successfully")

###############################################################################################
# ReAct Agent V2

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
            "max_tokens": 2000,
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
        tools = []
        tools.append(WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper(top_k_results=2)))
        tools.append(DuckDuckGoSearchRun())
        return tools

    def create_agent(model, tools):
        memory = MemorySaver()
        instructions = """You are a helpful AI assistant. Answer questions clearly and concisely."""
        return create_react_agent(model, tools=tools, checkpointer=memory, state_modifier=instructions)

    def convert_messages(messages):
        return [
            HumanMessage(content=msg["content"]) if msg["role"] == "user" 
            else AIMessage(content=msg["content"])
            for msg in messages
        ]

    def generate(context):
        payload = context.get_json()
        messages = convert_messages(payload.get("messages", []))
        
        model_instance = create_chat_model(client)
        tools = create_tools()
        agent = create_agent(model_instance, tools)
        
        response = agent.invoke(
            {"messages": messages},
            {"configurable": {"thread_id": "42"}}
        )
        
        return {
            "headers": {"Content-Type": "application/json"},
            "body": {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": response["messages"][-1].content
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
        {"role": "user", "content": "provide 2 real world metrics of analyzing business workflow inefficiencies at fast growing startups."}
        # sample query: provide 2 real world metrics of analyzing business workflow inefficiencies at fast growing startups.
    ]
    context = RealContext(messages)
    generate, _ = gen_ai_service(context)
    response = generate(context)
    print(json.dumps(response, indent=2))
