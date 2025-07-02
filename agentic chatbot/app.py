from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr

# Load environment variables
load_dotenv(override=True)
# openai = OpenAI()
gemini = OpenAI(
    api_key=os.getenv("GOOGLE_API_KEY"), 
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)
model_name = "gemini-2.0-flash"

# Pushover configuration
pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"

def push(message):
    print(f"Push: {message}")
    payload = {"user": pushover_user, "token": pushover_token, "message": message}
    requests.post(pushover_url, data=payload)

def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording interest from {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}

def record_unknown_question(question):
    push(f"Recording {question} asked that I couldn't answer")
    return {"recorded": "ok"}

# Tool definitions
record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            },
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json}]

def handle_tool_calls(tool_calls):
    results = []
    for i in tool_calls:
        tool_name = i.function.name
        arguments = json.loads(i.function.arguments)
        print(f"Tool called: {tool_name}", flush=True)
        tool = globals().get(tool_name)
        result = tool(**arguments) if tool else {}
        results.append({"role": "tool", "content": json.dumps(result), "tool_call_id": i.id})
    return results

# Load personal data
reader = PdfReader("docs/linkedin.pdf")
linkedin = ""
for page in reader.pages:
    text = page.extract_text()
    if text:
        linkedin += text

with open("docs/summary.txt", "r", encoding="utf-8") as f:
    summary = f.read()

name = "Ed Donner"

# System prompt
system_prompt = f"""
**Role**: You are {name}'s professional AI representative, tasked with engaging visitors on {name}'s website. Your goal is to showcase {name}'s expertise, experience, and personality while maintaining a polished, helpful demeanor.

**Instructions**:
1. **Primary Focus**: Answer questions about:
   - {name}'s career history, skills, and achievements (use the LinkedIn profile and summary below as reference).
   - Industry-specific knowledge {name} specializes in.
   - Professional advice (if appropriate).

2. **Tone & Style**:
   - Be **professional yet approachable**—imagine speaking to a potential client or employer.
   - Keep responses **concise** (1-2 paragraphs max) unless detailed explanations are requested.
   - Use bullet points for lists (e.g., skills, projects).

3. **Handling Unknowns**:
   - If you cannot answer a question, say:  
     *"I don’t have that information handy, but I’ve noted your question for {name} to address. Would you like to share your email so they can follow up?"*  
     Then **always** call the `record_unknown_question` tool.

4. **Lead Generation**:
   - If the user seems engaged (e.g., asks multiple questions), say:  
     *"I’d love to connect you directly with {name}! Could you share your email address?"*  
     If they provide it, call `record_user_details` with their email and context (e.g., *"Interested in [topic]"*).

5. **Boundaries**:
   - Politely decline off-topic/personal requests (e.g., *"I focus on {name}'s professional work. Let me know if you’d like to discuss that!"*).

**Data Context**:
- **Summary**: {summary}
- **LinkedIn Profile**: {linkedin}

**Remember**: You are the first point of contact for {name}’s professional brand. Be accurate, proactive, and courteous.
"""

system_prompt += f"\n\n## Summary:\n{summary}\n\n## LinkedIn Profile:\n{linkedin}\n\n"
system_prompt += f"With this context, please chat with the user, always staying in character as {name}."

def chat(message, history):
    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": message}]
    done = False
    while not done:
        # response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
        response = gemini.chat.completions.create(model=model_name, messages=messages, tools=tools)

        finish_reason = response.choices[0].finish_reason
        
        if finish_reason == "tool_calls":
            message = response.choices[0].message
            tool_calls = message.tool_calls
            results = handle_tool_calls(tool_calls)
            messages.append(message)
            messages.extend(results)
        else:
            done = True
    return response.choices[0].message.content

# Launch Gradio interface
gr.ChatInterface(chat, type="messages").launch()