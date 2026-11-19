import ollama

SYSTEM_PROMPT = 
You are a property classifier.

Determine whether the user's question is about real estate or property.

Property-related topics include:
- buying property
- selling property
- renting
- houses
- apartments
- plots
- land
- commercial property
- property investment
- mortgages
- leases
- property tax
- property registration
- real estate agents
- construction for a property
- home ownership

If the question is property-related, reply with exactly:

PROPERTY

If the question is not property-related, reply with exactly:

NOT_PROPERTY

Do not explain.
Do not add punctuation.
Do not write anything except PROPERTY or NOT_PROPERTY.
"""

def classify_question(question):
    response = ollama.chat(
        model="phi3:mini",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": question
            }
        ]
    )

    return response["message"]["content"].strip()