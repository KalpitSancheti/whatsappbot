import os
import traceback
from flask import Flask, request
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse
import requests
from langgraph.graph import StateGraph
from tools import all_tools  # <- from tools/__init__.py

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Flask app setup
app = Flask(__name__)

# Perplexity LLM

def call_perplexity(prompt):
    api_key = os.getenv("PERPLEXITY_API_KEY")
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "sonar-pro",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    result = response.json()
    return result["choices"][0]["message"]["content"]

# LangGraph state
class AgentState(dict):
    pass

# Custom fallback tool nodedef tools_to_tool_node(tools):
def tools_to_tool_node(tools):
    def node(state, event=None):
        print("[ToolNode] Raw state:", state)
        input_data = state.get("input", "") if state else ""
        print("[ToolNode] Received input:", input_data)

        new_state = dict(state) if state else {}
        new_state["input"] = input_data

        if not input_data:
            new_state["output"] = "Empty input received."
            return new_state

        for tool in tools:
            if tool.name.lower() in input_data.lower():
                try:
                    print(f"[ToolNode] Matching tool found: {tool.name}")
                    output = tool.invoke(input_data)
                    new_state["output"] = output
                    return new_state
                except Exception as e:
                    print(f"[ToolNode Error] {tool.name} failed: {e}")
                    new_state["output"] = f"Tool '{tool.name}' error: {e}"
                    return new_state

        # Multi-step AI-driven tool chaining with Perplexity
        try:
            print("[ToolNode] No tool matched, starting multi-step tool chaining with Perplexity")
            tool_descriptions = """
You are an advanced assistant with access to these tools:

- calendar: Add a meeting or reminder to Google Calendar. Input: JSON with title, description, date (YYYY-MM-DD), start_time (HH:MM or ISO 8601), and end_time (HH:MM or ISO 8601). If only a start_time is given, assume 1 hour duration unless the event type suggests otherwise (e.g., drinking water is 5 minutes, bath is 30 minutes, meeting is 1 hour, fill form is 30 minutes, send email is 15 minutes, submit assignment is 15 minutes, etc.). For tasks like 'fill form', 'submit assignment', 'send email', or other quick reminders, use a default duration of 15–30 minutes unless the user specifies otherwise. Output: Confirmation or error.

- calendar_query: Fetch all events and free slots for a specified day (input: 'YYYY-MM-DD', 'today', or 'tomorrow'). Output: JSON with date, events (summaries with start/end), free_slots (list of 1-hour free blocks between 8:00 and 22:00), and slot_status (mapping of each hour to 'free' or 'busy: <event>'). Use this tool to get context before scheduling, suggesting free times, or answering about the day's agenda.

- calendar_delete: Delete a meeting or reminder from Google Calendar. Input: JSON with title and date (YYYY-MM-DD) of the event to delete. Output: Confirmation or error. Use this tool whenever the user says 'cancel', 'delete', 'remove', or 'change the slot' for a meeting or reminder. If the user wants to reschedule, first delete the old event, then create a new one with the updated time. If the user says 'cancel it', 'remove my 8 pm meeting', or 'change my 10 am reminder to 11 am', use this tool to delete the relevant event before making changes.

- time: Tell the current time. Input: any string (ignored). Output: current date and time in Asia/Kolkata timezone. Use this tool if you need to know the current time to answer or schedule.

- echo: Echo back the user's message. Input: any string. Output: the same string.

How to use tools:
- If the user asks about their schedule, free slots, or meetings for a day, use calendar_query.
- If the user wants to schedule something, use calendar_query first to get free slots, then use calendar to add the event in a free slot.
- If the user asks to schedule, book, or set up a meeting or event, DO NOT ask for confirmation. Always use the calendar_query tool to check for free slots before scheduling. Only schedule an event in a slot that is confirmed to be free. If the requested slot is not free, suggest the next available slot. Always pick the first available free slot in the requested time range (e.g., 'evening' means 17:00-22:00) and schedule the event using the calendar tool. Only ask for confirmation if the user's request is ambiguous or if there are conflicting events. You MUST always call the calendar tool to actually schedule the event, and only confirm the booking after you have received the tool result. Never confirm a booking unless the calendar tool has been called and has returned a successful result. If you have just received a calendar_query result and the user's intent was to schedule, you MUST always call the calendar tool to actually schedule the event in a free slot. Never answer with general information or code samples—always proceed to schedule the event using the tool.
- If you need to know the current time to answer, use the time tool.
- Always provide clear, user-friendly responses after tool calls.

Example:
User: schedule a meeting in the evening with yug today
Assistant: (calls calendar_query for today, finds free slots, then immediately calls calendar to schedule the meeting in the first available evening slot, e.g., 17:00-18:00, and confirms the booking to the user)

User: add a reminder to fill form at 3 pm
Assistant: (calls calendar tool with start_time 15:00, end_time 15:30)

User: set up a play session at 10pm today
Assistant: (calls calendar_query for today, finds free slots, then calls calendar tool to schedule the event at 22:00-23:00, and only then confirms the booking to the user)

User: schedule a meet at 8 pm today
Assistant: (calls calendar_query for today, finds free slots, then calls calendar tool to schedule the event at 20:00-21:00, and only then confirms the booking to the user)

User: cancel my 8 pm meeting today
Assistant: (calls calendar_delete tool with title 'meeting' and date for today, confirms deletion)

User: change my 10 am reminder to 11 am
Assistant: (calls calendar_delete tool to remove the 10 am reminder, then calls calendar tool to create a new reminder at 11 am)

If you want to use a tool, respond with:
TOOL_CALL: <tool_name> | <arguments>
Otherwise, answer normally.
After any tool is called, you will be shown the tool's result. Respond to the user with a helpful, natural message based on the tool result.
"""
            conversation = [
                {"role": "system", "content": tool_descriptions},
                {"role": "user", "content": input_data}
            ]
            max_steps = 5
            for step in range(max_steps):
                prompt = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in conversation])
                perplexity_response = call_perplexity(prompt)
                print(f"[ToolNode] Perplexity response (step {step+1}): {perplexity_response}")
                if "TOOL_CALL:" in perplexity_response:
                    try:
                        tool_call = perplexity_response.split("TOOL_CALL:",1)[1].strip()
                        tool_name, tool_args = tool_call.split("|", 1)
                        tool_name = tool_name.strip().lower()
                        tool_args = tool_args.strip()
                        for tool in tools:
                            if tool.name.lower() == tool_name:
                                print(f"[ToolNode] About to call tool: {tool.name} with args: {tool_args}", flush=True)
                                output = tool.invoke(tool_args)
                                conversation.append({"role": "tool", "content": f"{tool.name} result: {output}"})
                                # After any tool call, prompt Perplexity for the final user message
                                if tool.name == "calendar" or tool.name == "time" or tool.name == "echo":
                                    # Ask Perplexity to generate the final user message
                                    prompt2 = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in conversation])
                                    final_response = call_perplexity(prompt2)
                                    print(f"[ToolNode] Perplexity final user message: {final_response}")
                                    new_state["output"] = final_response
                                    return new_state
                                else:
                                    break
                        else:
                            new_state["output"] = f"Tool '{tool_name}' not found."
                            return new_state
                    except Exception as e:
                        print(f"[ToolNode Error] Tool call parsing failed: {e}")
                        new_state["output"] = f"Tool call parsing error: {e}"
                        return new_state
                else:
                    new_state["output"] = perplexity_response
                    return new_state
            else:
                new_state["output"] = "Tool chaining exceeded max steps."
        except Exception as e:
            print(f"[ToolNode Error] Perplexity failed: {e}")
            new_state["output"] = f"Perplexity error: {e}"
        return new_state
    return node





# Build LangGraph
tool_node = tools_to_tool_node(all_tools)
workflow = StateGraph(dict)
workflow.add_node("tools", tool_node)
workflow.set_entry_point("tools")
workflow.set_finish_point("tools")
graph_executor = workflow.compile()

# WhatsApp webhook route
@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    print("[Form Data]", dict(request.form))

    incoming_msg = request.form.get("Body", "").strip()
    print(f"[User] {incoming_msg}")

    try:
        print("[DEBUG] About to invoke graph_executor with:", {"input": incoming_msg})
        result = graph_executor.invoke({"input": incoming_msg})
        print("[DEBUG] Type of result:", type(result))
        print("[LangGraph Result]", result)

        if not result or not isinstance(result, dict):
            raise ValueError("LangGraph returned no result or invalid structure")

        response_text = result.get("output", "Sorry, no output.")

    except Exception as e:
        import traceback
        print("[Exception]", traceback.format_exc())
        response_text = "Sorry, something went wrong."

    resp = MessagingResponse()
    resp.message(response_text)
    return str(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)