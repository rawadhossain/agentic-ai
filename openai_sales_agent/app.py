from dotenv import load_dotenv
from agents import Agent, Runner, trace, function_tool
from openai.types.responses import ResponseTextDeltaEvent
from typing import Dict
import sendgrid
import os
from sendgrid.helpers.mail import Mail, Email, To, Content
import asyncio

load_dotenv(override=True)

def send_test_email():
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    from_email = Email("ed@edwarddonner.com")  # Change to your verified sender
    to_email = To("ed.donner@gmail.com")  # Change to your recipient
    content = Content("text/plain", "This is an important test email")
    mail = Mail(from_email, to_email, "Test email", content).get()
    response = sg.client.mail.send.post(request_body=mail)
    print(response.status_code)

send_test_email()

instructions1 = "You are a sales agent working for ComplAI, \
a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. \
You write professional, serious cold emails."

instructions2 = "You are a humorous, engaging sales agent working for ComplAI, \
a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. \
You write witty, engaging cold emails that are likely to get a response."

instructions3 = "You are a busy sales agent working for ComplAI, \
a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. \
You write concise, to the point cold emails."

sales_agent1 = Agent(
        name="Professional Sales Agent",
        instructions=instructions1,
        model="gpt-4o-mini"
)

sales_agent2 = Agent(
    name="Engaging Sales Agent",
    instructions=instructions2,
    model="gpt-4o-mini"
)

sales_agent3 = Agent(
    name="Busy Sales Agent",
    instructions=instructions3,
    model="gpt-4o-mini"
)

async def run_sales_agents():
    result = Runner.run_streamed(sales_agent1, input="Write a cold sales email")
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            print(event.data.delta, end="", flush=True)

    message = "Write a cold sales email"

    with trace("Parallel cold emails"):
        results = await asyncio.gather(
            Runner.run(sales_agent1, message),
            Runner.run(sales_agent2, message),
            Runner.run(sales_agent3, message)
        )

        outputs = [result.final_output for result in results]

        for output in outputs:
            print(output + "\n\n")

sales_picker = Agent(
    name="sales_picker",
    instructions="You pick the best cold sales email from the given options. "
                "Imagine you are a customer and pick the one you are most likely to respond to. "
                "Do not give an explanation; reply with the selected email only.",
    model="gpt-4o-mini"
)

async def run_sales_picker():
    message = "Write a cold sales email"
    with trace("Selection from sales people"):
        results = await asyncio.gather(
            Runner.run(sales_agent1, message),
            Runner.run(sales_agent2, message),
            Runner.run(sales_agent3, message)
        )

        outputs = [result.final_output for result in results]
        for output in outputs:
            print(output + "\n\n")

# Call the asynchronous function
# asyncio.run(run_sales_picker())


async def run_sales_picker():
    sales_picker = Agent(
        name="sales_picker",
        instructions="You pick the best cold sales email from the given options. \
Imagine you are a customer and pick the one you are most likely to respond to. \
Do not give an explanation; reply with the selected email only.",
        model="gpt-4o-mini"
    )

    message = "Write a cold sales email"

    with trace("Selection from sales people"):
        results = await asyncio.gather(
            Runner.run(sales_agent1, message),
            Runner.run(sales_agent2, message),
            Runner.run(sales_agent3, message),
        )
        outputs = [result.final_output for result in results]

        emails = "Cold sales emails:\n\n".join(outputs)

        best = await Runner.run(sales_picker, emails)

        print(f"Best sales email:\n{best.final_output}")