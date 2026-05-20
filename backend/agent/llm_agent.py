import os
import json
from groq import AsyncGroq
from agent.tools import TOOLS_LIST, execute_tool
from memory.redis_store import SessionMemory

# Requires GROQ_API_KEY to be set in environment.
# User can get it for free from groq.com
client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY", "mock_key"))

SYSTEM_PROMPT = """You are a healthcare appointment assistant.
You speak English, Hindi, and Tamil. Always respond in the language the user speaks to you.
You must help the patient book, reschedule, or cancel appointments.
You have access to tools to manage the schedule. 
If the user wants to book, you need their preferred date, time, and doctor specialty. If they don't provide it, ask for it.
When you use a tool, you must inform the user of the result.
Keep responses very short and conversational.
CRITICAL: You must use the native JSON tool calling mechanism. DO NOT output `<function>` tags in your text response under any circumstances.
"""

class Agent:
    def __init__(self, session_id: str, patient_id: int):
        self.session = SessionMemory(session_id)
        self.patient_id = patient_id
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        
    async def process_text(self, text: str) -> str:
        self.messages.append({"role": "user", "content": text})
        
        # In a real app, you would retrieve past history here
        # past_history = get_patient_history(self.patient_id)
        
        # Call Groq LLM (Llama 3 is very fast for this)
        try:
            response = await client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=self.messages,
                tools=TOOLS_LIST,
                tool_choice="auto"
            )
            
            response_message = response.choices[0].message
            
            # Check if tool calls exist
            if response_message.tool_calls:
                self.messages.append(response_message)
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    tool_result = execute_tool(function_name, function_args, self.patient_id)
                    
                    self.messages.append({
                        "role": "tool",
                        "name": function_name,
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    })
                
                # Second call to get final text response after tool
                final_response = await client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=self.messages
                )
                final_text = final_response.choices[0].message.content
                self.messages.append({"role": "assistant", "content": final_text})
                return final_text
            else:
                reply = response_message.content
                import re
                match = re.search(r'<function=([^>]+)>(.*?)</function>', reply, re.DOTALL)
                if match:
                    # Fallback for models leaking XML tool calls
                    func_name = match.group(1)
                    try:
                        func_args = json.loads(match.group(2))
                        tool_result = execute_tool(func_name, func_args, self.patient_id)
                        
                        # Since it didn't use native tools, we feed the result back as a system observation
                        self.messages.append({"role": "assistant", "content": reply})
                        self.messages.append({"role": "user", "content": f"System Observation from tool: {tool_result}"})
                        
                        final_response = await client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=self.messages
                        )
                        final_text = final_response.choices[0].message.content
                        self.messages.append({"role": "assistant", "content": final_text})
                        return final_text
                    except Exception as e:
                        pass
                
                self.messages.append({"role": "assistant", "content": reply})
                return reply
        except Exception as e:
            print(f"LLM Error: {e}")
            if "api_key" in str(e).lower() or "unauthorized" in str(e).lower():
                return "System Error: Please configure a valid GROQ_API_KEY in the backend."
            return "I'm having trouble processing that request. Could you repeat?"
