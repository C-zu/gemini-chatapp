import os
from typing import Any, List, Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from google.generativeai.types.safety_types import HarmBlockThreshold, HarmCategory

class ChatModel:
    """Wrapper for Gemini chat model with memory"""

    def __init__(self, model_name="gemini-1.5-flash", temperature=0.3):
        self.model_name = model_name
        self.temperature = temperature
        self.llm = self._load_model(model_name)
        self.system_message = SystemMessage(content="You are a helpful assistant.")

    def _load_model(self, model_name):
        if "gemini" in model_name:
            safety_settings = {
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            }
            return ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=os.getenv("GOOGLE_API_KEY"),
                temperature=self.temperature,
                safety_settings=safety_settings,
                streaming=True
            )
        else:
            raise ValueError(f"Unsupported model: {model_name}")
    
    def chat(self, user_input: str, chat_history: List) -> str:
        """Chat with memory - receive chat_history as list of HumanMessage/AIMessage"""
        print("Chat history:", chat_history)
        
        # Build messages - chat_history is already List[HumanMessage/AIMessage]
        messages = [self.system_message]
        messages.extend(chat_history)
        messages.append(HumanMessage(content=user_input))  # Add current message

        # Get response
        response = self.llm.stream(messages).content
        
        # 🆕 Return response, memory update will be handled by caller
        return response
    
    def chat_with_image(self, user_input: str, image_data: str, chat_history: List) -> str:
        """Chat with image - receive chat_history as list of HumanMessage/AIMessage"""
        
        # Build content with image
        content = [
            {"type": "text", "text": user_input},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
        ]
        
        # Build messages for LLM
        messages = [self.system_message]
        messages.extend(chat_history)  # Use passed chat_history
        messages.append(HumanMessage(content=content))

        # Get response
        response = self.llm.stream(messages).content
        
        # 🆕 Return response, memory update will be handled by caller
        return response