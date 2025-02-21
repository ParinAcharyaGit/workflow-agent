import asyncio
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from beeai_framework.adapters.watsonx.backend.chat import WatsonxChatModel
from beeai_framework.backend.message import UserMessage
from beeai_framework.cancellation import AbortSignal
from azureml.core import ScriptRunContext  

# Load environment variables from .env file
load_dotenv()

# Retrieve the values from environment variables
project_id = os.getenv("WATSONX_PROJECT_ID")
api_key = os.getenv("WATSONX_API_KEY")
api_base = os.getenv("WATSONX_API_URL")

context = ScriptRunContext()  # Adjust this line based on your actual context initialization

# Initialize the WatsonxChatModel with IBM Granite
llm = WatsonxChatModel(
    "ibm/granite-3-8b-instruct",
    project_id=project_id,
    api_key=api_key,
    api_base=api_base,
)

async def watsonx_sync() -> None:
    user_message = UserMessage("What is the capital of Massachusetts?")
    try:
        response = await llm.create({"messages": [user_message]})
        print(response.get_text_content())
    except Exception as ex:
        await context.emitter.emit("error", {"input": [user_message], "exception": str(ex)})

async def watsonx_stream() -> None:
    user_message = UserMessage("How many islands make up the country of Cape Verde?")
    try:
        response = await llm.create({"messages": [user_message], "stream": True})
        print(response.get_text_content())
    except Exception as ex:
        await context.emitter.emit("error", {"input": [user_message], "exception": str(ex)})

async def watsonx_stream_abort() -> None:
    user_message = UserMessage("What is the smallest of the Cape Verde islands?")
    try:
        response = await llm.create({"messages": [user_message], "stream": True, "abort_signal": AbortSignal.timeout(0.5)})
        if response is not None:
            print(response.get_text_content())
        else:
            print("No response returned.")
    except Exception as ex:
        await context.emitter.emit("error", {"input": [user_message], "exception": str(ex)})

async def watson_structure() -> None:
    class TestSchema(BaseModel):
        answer: str = Field(description="your final answer")

    user_message = UserMessage("How many islands make up the country of Cape Verde?")
    response = await llm.create_structure(
        {
            "schema": TestSchema,
            "messages": [user_message],
        }
    )
    print(response.object)

async def main() -> None:
    print("*" * 10, "watsonx_sync")
    await watsonx_sync()
    print("*" * 10, "watsonx_stream")
    await watsonx_stream()
    print("*" * 10, "watsonx_stream_abort")
    await watsonx_stream_abort()
    print("*" * 10, "watson_structure")
    await watson_structure()

if __name__ == "__main__":
    asyncio.run(main())