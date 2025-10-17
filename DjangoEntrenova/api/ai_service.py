# api/ai_service.py

import os
import google.generativeai as genai

class GeminiService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("A chave da API do Gemini não foi configurada no servidor")
        
        genai.configure(api_key=api_key)

    def _format_history(self, history_from_frontend):
        api_history = []
        for message in history_from_frontend:
            if message.get('role') and message.get('text'):
                api_history.append({
                    'role': message['role'],
                    'parts': [{'text': message['text']}]
                })
        return api_history

    def start_chat_session(self, system_prompt, history=[]):
        model = genai.GenerativeModel(
            model_name="gemini-2.5-pro", 
            system_instruction=system_prompt
        )
        
        formatted_history = self._format_history(history)
        chat_session = model.start_chat(history=formatted_history)
        return chat_session
    
try:
    gemini_service = GeminiService()
except ValueError as e:
    print(f"Erro ao inicializar o GeminiService: {e}")
    gemini_service = None

class GeminiServiceFlash:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("A chave da API do Gemini não foi configurada no servidor")
        
        genai.configure(api_key=api_key)

    def _format_history(self, history_from_frontend):
        api_history = []
        for message in history_from_frontend:
            if message.get('role') and message.get('text'):
                api_history.append({
                    'role': message['role'],
                    'parts': [{'text': message['text']}]
                })
        return api_history

    def start_chat_session(self, system_prompt, history=[]):
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-001", 
            system_instruction=system_prompt
        )
        
        formatted_history = self._format_history(history)
        chat_session = model.start_chat(history=formatted_history)
        return chat_session
    
try:
    gemini_service = GeminiService()
except ValueError as e:
    print(f"Erro ao inicializar o GeminiService: {e}")
    gemini_service = None
    
    

