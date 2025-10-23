import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from google.generativeai.types.safety_types import HarmBlockThreshold, HarmCategory
from langchain.agents import tool
from plotly.graph_objects import Figure
from plotly.io import from_json
import json

class AIService:
    def __init__(self, model_name="gemini-2.5-flash", temperature=0.3):
        self.model_name = model_name
        self.temperature = temperature
        self.llm = self._load_model(model_name)
        self.system_message = SystemMessage(content="You are a helpful assistant.")

    def _load_model(self, model_name):
        """Load Gemini model with safety settings"""
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

    def _prepare_chat_history(self, chat_history):
        """Convert schema messages to LangChain messages"""
        messages = []
        for msg in chat_history:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))
        return messages

    def generate_text_response(self, user_input, chat_history):
        """Generate text response with history"""
        # Prepare messages
        messages = [self.system_message]
        messages.extend(self._prepare_chat_history(chat_history))
        messages.append(HumanMessage(content=user_input))
        
        return self.llm.stream(messages)

    def generate_image_response(self, user_input, image_data, chat_history):
        """Generate response for image analysis"""
        # Build content with image
        content = [
            {"type": "text", "text": user_input},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
        ]
        
        # Prepare messages
        messages = [self.system_message]
        messages.extend(self._prepare_chat_history(chat_history))
        messages.append(HumanMessage(content=content))
        
        return self.llm.stream(messages)
    def generate_csv_response(self, enhanced_query: str, dataframe=None, session_id=None) -> str:
        """Generate response for CSV analysis using pandas agent with plotting capability"""
        try:
            if dataframe is None:
                return "❌ No dataset available. Please upload a CSV file first."
            
            # Clear previous plots for this session
            if session_id:
                if session_id not in self.plots_storage:
                    self.plots_storage[session_id] = []
                else:
                    self.plots_storage[session_id] = []  # Clear existing plots
            
            agent = self._get_or_create_agent(dataframe, session_id)
            response = agent.run(enhanced_query)
            return response
            
        except Exception as e:
            return f"❌ Error analyzing CSV data: {str(e)}"
# Global instance
ai_service = AIService()