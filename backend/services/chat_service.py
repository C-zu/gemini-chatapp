from typing import List, Dict, Any

from models.schemas import ChatMessage
from .chat_repository import chat_repo
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
import os
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain.agents import tool
from plotly.graph_objects import Figure
from plotly.io import from_json
import json

class ChatService:
    def __init__(self):
        self.repository = chat_repo
    
    def create_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.repository.create_session(session_data)
    
    def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        return self.repository.get_session_messages(session_id)
    
    def add_message(self, session_id: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.repository.add_message(session_id, message_data)
    
    def get_all_sessions(self) -> Dict[str, Any]:
        return self.repository.get_all_sessions()
    
    def delete_session(self, session_id: str) -> bool:
        return self.repository.delete_session(session_id)
    
    def save_session_file(self, session_id: str, file_type: str, file_data: Dict[str, Any], file_name: str = None) -> Dict[str, Any]:
        return self.repository.save_session_file(session_id, file_type, file_data, file_name)
    
    def get_session_file(self, session_id: str, file_type: str) -> Dict[str, Any]:
        return self.repository.get_session_file(session_id, file_type)

class AIService:
    def __init__(self):
        self.llm = self._load_model()
        self.system_message = SystemMessage(content="You are a helpful assistant.")
        self.agents = {}
        self.plots_storage = {}
    def _load_model(self):
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.3,
            streaming=True
        )
    def convert_to_langchain_messages(self, messages: List[ChatMessage]) -> List:
        """Convert custom ChatMessage objects to LangChain messages"""
        langchain_messages = []
        for msg in messages:
            if msg.role == "user":
                langchain_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                langchain_messages.append(AIMessage(content=msg.content))
            elif msg.role == "system":
                langchain_messages.append(SystemMessage(content=msg.content))
            else:
                langchain_messages.append(HumanMessage(content=msg.content))
        return langchain_messages
    def generate_text_response(self, user_input, chat_history):
        """Generate text response with history"""
        messages = [self.system_message]
        chat_history = self.convert_to_langchain_messages(chat_history)
        messages.extend(chat_history)
        messages.append(HumanMessage(content=user_input))
        response = self.llm.stream(messages)
        for chunk in response:
            yield chunk
    
    def generate_image_response(self, user_input, image_data, chat_history):
        """Generate response for image analysis"""
        content = [
            {"type": "text", "text": user_input},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
        ]
        chat_history = self.convert_to_langchain_messages(chat_history)
        messages = [self.system_message]
        messages.extend(chat_history)
        messages.append(HumanMessage(content=content))
        
        return self.llm.stream(messages)
    def generate_csv_response(self, enhanced_query: str, dataframe=None, session_id=None) -> str:
        """Generate response for CSV analysis using pandas agent"""
        try:
            if dataframe is None:
                return "❌ No dataset available. Please upload a CSV file first."
            # Clear previous plots for this session
            if session_id:
                self.plots_storage[session_id] = []
            
            agent = self._get_or_create_agent(dataframe, session_id)
            
            response = agent.run(enhanced_query)
            
            return response
            
        except Exception as e:
            return f"❌ Error analyzing CSV data: {str(e)}"

    def _get_or_create_agent(self, dataframe, session_id=None):
        """Get existing agent or create new one with plot tools"""
        try:
            if session_id and session_id in self.agents:
                return self.agents[session_id]
            plot_tools = self._create_plot_tools(session_id)
            
            agent = create_pandas_dataframe_agent(
                self.llm,
                dataframe,
                verbose=True,
                handle_parsing_errors=True,
                allow_dangerous_code=True,  
                agent_type="openai-tools",  
                max_iterations=3,  # Reduce for testing
                early_stopping_method="generate", 
                return_intermediate_steps=False,
                extra_tools=plot_tools
            )
            
            if session_id:
                self.agents[session_id] = agent
            
            return agent
            
        except Exception as e:
            raise Exception(f"Error creating agent: {str(e)}")
    def _create_plot_tools(self, session_id=None):
        """Create plotting tools for the agent"""
        try:
            @tool
            def plotChart(data: str) -> str:
                """Plots json data using plotly Figure. Use it only for plotting charts and graphs."""
                try:
                    figure_dict = json.loads(data)
                    fig = from_json(json.dumps(figure_dict))
                    
                    if session_id:
                        if session_id not in self.plots_storage:
                            self.plots_storage[session_id] = []
                        self.plots_storage[session_id].append(fig)
                    
                    return "Chart created successfully and will be displayed to the user."
                    
                except Exception as e:
                    return f"Error plotting chart: {str(e)}"
            
            return [plotChart]
            
        except Exception as e:
            return []
    
    def get_plots(self, session_id):
        """Get plots for a specific session with debugging"""
        try:
            if session_id in self.plots_storage:
                plots = self.plots_storage[session_id].copy()
                print(f"📊 Found {len(plots)} plots in storage")
                
                for i, plot in enumerate(plots):
                    print(f"   Plot {i+1}: type={type(plot)}, has_to_dict={hasattr(plot, 'to_dict')}, has_to_json={hasattr(plot, 'to_json')}")
                    
                return plots
            print(f"📊 No plots found for session {session_id}")
            return []
        except Exception as e:
            print(f"❌ Error getting plots: {e}")
            return []

    def clear_plots(self, session_id):
        """Clear plots for a specific session"""
        try:
            if session_id in self.plots_storage:
                self.plots_storage[session_id] = []
        except Exception as e:
            pass

ai_service = AIService()

chat_service = ChatService()