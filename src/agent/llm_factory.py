import os
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

class AzureLLMs:
    def __init__(self, temperature: int = 0):
        from langchain_openai import AzureChatOpenAI

        self._azure_llm = AzureChatOpenAI(
                        openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
                        azure_deployment=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
                        temperature=temperature,
                        max_tokens=None,
                    )
        
    def get_llm(self):
        return self._azure_llm

class OllamaLLMs:
    def __init__(self):
        from langchain_community.llms import Ollama

        self._ollama_llm = Ollama(
            model=os.environ['OLLAMA_MODEL'],
            base_url=os.environ['OLLAMA_BASE_URL'],
            headers={
                'X-API-Key': os.environ['OLLAMA_API_KEY'],
            },
        )

    def get_llm(self):
        return self._ollama_llm

class OpenAILLMs:
    def __init__(self, temperature: int = 0):
        from langchain_openai import ChatOpenAI

        self._openai_llm = ChatOpenAI(
            model=os.environ['OPENAI_MODEL'],
            temperature=temperature,
            api_key=os.environ["OPENAI_API_KEY"],
        )

    def get_llm(self):
        return self._openai_llm

class GoogleAILLMs:
    def __init__(self, temperature: int = 0):
        from langchain_google_genai import ChatGoogleGenerativeAI

        self._google_llm = ChatGoogleGenerativeAI(
            model=os.environ['GOOGLE_AI_MODEL'],
            temperature=temperature,
            google_api_key=os.environ['GOOGLE_AI_API_KEY'],
        )

    def get_llm(self):
        return self._google_llm

class OpenRouterLLMs:
    def __init__(self, temperature: int = 0, model: Optional[str] = None):
        from langchain_openai import ChatOpenAI

        model_name = model or os.environ['OPENROUTER_MODEL']
        key = os.environ['OPENROUTER_API_KEY']
        base_url = os.environ['OPENROUTER_BASE_URL']

        self._openrouter_llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=key,
            base_url=base_url,
        )

    def get_llm(self):
        return self._openrouter_llm