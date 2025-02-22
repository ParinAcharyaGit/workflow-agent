import os
import json
from dotenv import load_dotenv

load_dotenv()

params = {
    "space_id": "825b15ec-b09f-413c-80ed-4e7fd3fc0bb0",
    "vector_index_id": "812bdd89-66c9-47b9-9916-fe8fe3cd30f1"
}


def gen_ai_service(context, params=params, **custom):
    from langchain_ibm import ChatWatsonx
    from ibm_watsonx_ai import APIClient
    from langchain_core.messages import AIMessage, HumanMessage
    from langchain.tools import WikipediaQueryRun
    from langchain_community.utilities import WikipediaAPIWrapper
    from langchain_community.tools import DuckDuckGoSearchRun
    from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.prebuilt import create_react_agent
    import json

    model = "meta-llama/llama-3-3-70b-instruct"
    service_url = "https://us-south.ml.cloud.ibm.com"

    credentials = {
        "url": service_url,
        "token": context.generate_token()
    }

    client = APIClient(credentials)
    space_id = params.get("space_id")
    client.set.default_space(space_id)
    vector_index_id = params.get("vector_index_id")

    vector_index_details = client.data_assets.get_details(vector_index_id)
    vector_index_properties = vector_index_details["entity"]["vector_index"]
    top_n = 20 if vector_index_properties["settings"].get("rerank") else int(vector_index_properties["settings"]["top_k"])

    def rerank(client, documents, query, top_n):
        from ibm_watsonx_ai.foundation_models import Rerank

        reranker = Rerank(
            model_id="cross-encoder/ms-marco-minilm-l-12-v2",
            api_client=client,
            params={
                "return_options": {"top_n": top_n},
                "truncate_input_tokens": 512
            }
        )
        reranked_results = reranker.generate(query=query, inputs=documents)["results"]
        new_documents = []
        for result in reranked_results:
            result_index = result["index"]
            new_documents.append(documents[result_index])
        return new_documents

    import gzip
    import chromadb
    import random
    import string

    def hydrate_chromadb():
        data = client.data_assets.get_content(vector_index_id)
        content = gzip.decompress(data)
        stringified_vectors = str(content, "utf-8")
        vectors = json.loads(stringified_vectors)
        chroma_client = chromadb.Client()
        collection_name = "my_collection"
        try:
            chroma_client.delete_collection(name=collection_name)
        except Exception:
            print("Collection didn't exist - nothing to do.")
        collection = chroma_client.create_collection(name=collection_name)
        vector_embeddings = []
        vector_documents = []
        vector_metadatas = []
        vector_ids = []
        for vector in vectors:
            vector_embeddings.append(vector["embedding"])
            vector_documents.append(vector["content"])
            metadata = vector["metadata"]
            lines = metadata["loc"]["lines"]
            clean_metadata = {
                "asset_id": metadata["asset_id"],
                "asset_name": metadata["asset_name"],
                "url": metadata["url"],
                "from": lines["from"],
                "to": lines["to"]
            }
            vector_metadatas.append(clean_metadata)
            asset_id = metadata["asset_id"]
            random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            id_val = "{}:{}-{}-{}".format(asset_id, lines["from"], lines["to"], random_string)
            vector_ids.append(id_val)
        collection.add(
            embeddings=vector_embeddings,
            documents=vector_documents,
            metadatas=vector_metadatas,
            ids=vector_ids
        )
        return collection

    chroma_collection = hydrate_chromadb()

    from ibm_watsonx_ai.foundation_models.embeddings.sentence_transformer_embeddings import SentenceTransformerEmbeddings
    emb = SentenceTransformerEmbeddings('sentence-transformers/all-MiniLM-L6-v2')

    def proximity_search(question, inner_client, emb):
        query_vectors = emb.embed_query(question)
        query_result = chroma_collection.query(
            query_embeddings=query_vectors,
            n_results=top_n,
            include=["documents", "metadatas", "distances"]
        )
        documents = list(reversed(query_result["documents"][0]))
        if vector_index_properties["settings"].get("rerank"):
            documents = rerank(inner_client, documents, question, vector_index_properties["settings"]["top_k"])
        return "\n".join(documents)

    def create_chat_model(watsonx_client):
        parameters = {
            "frequency_penalty": 0,
            "max_tokens": 1000,
            "presence_penalty": 0,
            "temperature": 0,
            "top_p": 1
        }
        chat_model = ChatWatsonx(
            model_id=model,
            url=service_url,
            space_id=space_id,
            params=parameters,
            watsonx_client=watsonx_client,
        )
        return chat_model

    def get_schema_model(original_json_schema):
        from datamodel_code_generator import DataModelType, PythonVersion
        from datamodel_code_generator.model import get_data_model_types
        from datamodel_code_generator.parser.jsonschema import JsonSchemaParser
        from typing import Optional
        from pydantic import BaseModel, Field, constr
        import json
        json_schema = json.dumps(original_json_schema)
        data_model_types = get_data_model_types(
            DataModelType.PydanticV2BaseModel,
            target_python_version=PythonVersion.PY_311
        )
        parser = JsonSchemaParser(
            json_schema,
            data_model_type=data_model_types.data_model,
            data_model_root_type=data_model_types.root_model,
            data_model_field_type=data_model_types.field_model,
            data_type_manager_type=data_model_types.data_type_manager,
            dump_resolve_reference_action=data_model_types.dump_resolve_reference_action,
        )
        model_code = parser.parse()
        namespace = {"Field": Field, "constr": constr, "Optional": Optional}
        exec(model_code, namespace)
        exec("Model.model_rebuild()", namespace)
        pydantic_model = namespace['Model']
        return pydantic_model

    def get_remote_tool_descriptions():
        remote_tool_descriptions = {}
        remote_tool_schemas = {}
        import requests
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f'Bearer {context.generate_token()}'
        }
        tool_url = "https://private.api.dataplatform.cloud.ibm.com"
        remote_tools_response = requests.get(f'{tool_url}/wx/v1-beta/utility_agent_tools', headers=headers)
        remote_tools = remote_tools_response.json()
        for resource in remote_tools["resources"]:
            tool_name = resource["name"]
            tool_description = resource["description"]
            tool_schema = resource.get("input_schema")
            remote_tool_descriptions[tool_name] = tool_description
            if tool_schema:
                remote_tool_schemas[tool_name] = get_schema_model(tool_schema)
        return remote_tool_descriptions, remote_tool_schemas

    tool_descriptions, tool_schemas = get_remote_tool_descriptions()

    def create_remote_tool(tool_name, context):
        from langchain_core.tools import StructuredTool, Tool
        import requests

        def call_tool(tool_input):
            body = {"tool_name": tool_name, "input": tool_input}
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f'Bearer {context.get_token()}'
            }
            tool_url = "https://private.api.dataplatform.cloud.ibm.com"
            tool_response = requests.post(f'{tool_url}/wx/v1-beta/utility_agent_tools/run', headers=headers, json=body)
            if tool_response.status_code > 400:
                raise Exception(f'Error calling remote tool: {tool_response.json()}')
            return tool_response.json().get("output")

        def call_tool_structured(**tool_input):
            return call_tool(tool_input)

        def call_tool_unstructured(tool_input):
            return call_tool(tool_input)

        remote_tool_schema = tool_schemas.get(tool_name)
        if remote_tool_schema:
            tool = StructuredTool(
                name=tool_name,
                description=tool_descriptions[tool_name],
                func=call_tool_structured,
                args_schema=remote_tool_schema
            )
            return tool
        tool = Tool(
            name=tool_name,
            description=tool_descriptions[tool_name],
            func=call_tool_unstructured
        )
        return tool

    def create_custom_tool(tool_name, tool_description, tool_code, tool_schema):
        from langchain_core.tools import StructuredTool
        import ast

        def call_tool(**kwargs):
            tree = ast.parse(tool_code, mode="exec")
            function_name = tree.body[0].name
            compiled_code = compile(tree, 'custom_tool', 'exec')
            namespace = {}
            exec(compiled_code, namespace)
            return namespace[function_name](**kwargs)

        tool = StructuredTool(
            name=tool_name,
            description=tool_description,
            func=call_tool,
            args_schema=get_schema_model(tool_schema)
        )
        return tool

    def create_custom_tools():
        custom_tools = []

    def create_tools(inner_client, context):
        tools = []
        top_k_results = 5
        wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper(top_k_results=top_k_results))
        tools.append(wikipedia)

        def proximity_search_wrapper(question):
            return proximity_search(question, inner_client, emb)

        from langchain_core.tools import Tool
        rag_query = Tool(
            name="RAGQuery",
            description="Search information in documents to provide context to a user query. Useful when asked to ground the answer in specific knowledge about test_data.",
            func=proximity_search_wrapper
        )
        tools.append(rag_query)
        tools.append(create_remote_tool("GoogleSearch", context))
        tools.append(create_remote_tool("WebCrawler", context))
        return tools

    def create_agent(model, tools, messages):
        memory = MemorySaver()
        instructions = """
# Notes
- Use markdown syntax for formatting code snippets, links, JSON, tables, images, files.
- Any HTML tags must be wrapped in block quotes, for example ```<html>```.
- When returning code blocks, specify language.
- Sometimes, things don't go as planned. Tools may not provide useful information on the first few tries. You should always try a few different approaches before declaring the problem unsolvable.
- When the tool doesn't give you what you were asking for, you must either use another tool or a different tool input.
- When using search engines, you try different formulations of the query, possibly even in a different language.
- You cannot do complex calculations, computations, or data manipulations without using tools.
- If you need to call a tool to compute something, always call it.
  
If a tool returns an IMAGE in the result, include it as Markdown.

Example:

Tool result: IMAGE(https://api.dataplatform.cloud.ibm.com/wx/v1-beta/utility_agent_tools/cache/images/plt-04e3c91ae04b47f8934a4e6b7d1fdc2c.png)
Markdown to return: ![Generated image](https://api.dataplatform.cloud.ibm.com/wx/v1-beta/utility_agent_tools/cache/images/plt-04e3c91ae04b47f8934a4e6b7d1fdc2c.png)

You are a helpful expert assistant that uses tools to answer questions about business workflow strategies.
When greeted, say "Hi, I am watsonx.ai agent for WorkWise AI. How can I help you?"
When asked about general questions, use web crawler and search engine tools to inform your answer.
Always ensure best practices."""
        for message in messages:
            if message["role"] == "system":
                instructions += message["content"]
        graph = create_react_agent(model, tools=tools, checkpointer=memory, state_modifier=instructions)
        return graph

    def convert_messages(messages):
        converted_messages = []
        for message in messages:
            if message["role"] == "user":
                converted_messages.append(HumanMessage(content=message["content"]))
            elif message["role"] == "assistant":
                converted_messages.append(AIMessage(content=message["content"]))
        return converted_messages

    def generate(context):
        payload = context.get_json()
        messages = payload.get("messages")
        inner_credentials = {
            "url": service_url,
            "token": context.get_token()
        }
        inner_client = APIClient(inner_credentials)
        model_instance = create_chat_model(inner_client)
        tools = create_tools(inner_client, context)
        agent = create_agent(model_instance, tools, messages)
        generated_response = agent.invoke(
            {"messages": convert_messages(messages)},
            {"configurable": {"thread_id": "42"}}
        )
        last_message = generated_response["messages"][-1]
        generated_response = last_message.content
        execute_response = {
            "headers": {"Content-Type": "application/json"},
            "body": {
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": generated_response
                    }
                }]
            }
        }
        return execute_response

    def generate_stream(context):
        print("Generate stream", flush=True)
        payload = context.get_json()
        messages = payload.get("messages")
        inner_credentials = {
            "url": service_url,
            "token": context.get_token()
        }
        inner_client = APIClient(inner_credentials)
        model_instance = create_chat_model(inner_client)
        tools = create_tools(inner_client, context)
        agent = create_agent(model_instance, tools, messages)
        response_stream = agent.stream(
            {"messages": messages},
            {"configurable": {"thread_id": "42"}},
            stream_mode=["updates", "messages"]
        )
        for chunk in response_stream:
            chunk_type = chunk[0]
            finish_reason = ""
            usage = None
            if chunk_type == "messages":
                message_object = chunk[1][0]
                if message_object.type == "AIMessageChunk" and message_object.content != "":
                    message = {"role": "assistant", "content": message_object.content}
                else:
                    continue
            elif chunk_type == "updates":
                update = chunk[1]
                if "agent" in update:
                    agent_data = update["agent"]
                    agent_result = agent_data["messages"][0]
                    if agent_result.additional_kwargs:
                        kwargs = agent_data["messages"][0].additional_kwargs
                        tool_call = kwargs["tool_calls"][0]
                        message = {
                            "role": "assistant",
                            "tool_calls": [{
                                "id": tool_call["id"],
                                "type": "function",
                                "function": {
                                    "name": tool_call["function"]["name"],
                                    "arguments": tool_call["function"]["arguments"]
                                }
                            }]
                        }
                    elif agent_result.response_metadata:
                        message = {"role": "assistant", "content": agent_result.content}
                        finish_reason = agent_result.response_metadata["finish_reason"]
                        if finish_reason:
                            message["content"] = ""
                        usage = {
                            "completion_tokens": agent_result.usage_metadata["output_tokens"],
                            "prompt_tokens": agent_result.usage_metadata["input_tokens"],
                            "total_tokens": agent_result.usage_metadata["total_tokens"]
                        }
                elif "tools" in update:
                    tools_data = update["tools"]
                    tool_result = tools_data["messages"][0]
                    message = {
                        "role": "tool",
                        "id": tool_result.id,
                        "tool_call_id": tool_result.tool_call_id,
                        "name": tool_result.name,
                        "content": tool_result.content
                    }
                else:
                    continue
            chunk_response = {"choices": [{"index": 0, "delta": message}]}
            if finish_reason:
                chunk_response["choices"][0]["finish_reason"] = finish_reason
            if usage:
                chunk_response["usage"] = usage
            yield chunk_response

    return generate, generate_stream


class RealContext:
    def __init__(self, messages):
        self._messages = messages
        self._token = os.getenv("WATSONX_TOKEN")
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
        {"role": "user", "content": "Hello, how can you help me?"}
    ]
    context = RealContext(messages)
    generate, _ = gen_ai_service(context)
    response = generate(context)
    print(json.dumps(response, indent=2))
