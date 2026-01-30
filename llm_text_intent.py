import json
import re
from llm_prompt import TEXT_INTENT_PROMPT
import streamlit as st
from chatbot import AZURE_OPENAI_CHAT_DEPLOYMENT_NAME



def extract_json(text: str) -> dict:
    """
    Safely extract JSON from LLM output.
    Handles markdown, newlines, and extra text.
    """
    if not text:
        raise ValueError("Empty LLM response")

    # remove markdown
    text = re.sub(r"```json", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)

    # find first JSON block
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError(f"No JSON found in response:\n{text}")

    try:
        return json.loads(match.group())
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON returned:\n{match.group()}") from e


def llm_parse_text_intent(client, question):
    response = client.chat.completions.create(
        model=AZURE_OPENAI_CHAT_DEPLOYMENT_NAME,
        messages=[
            {
                "role": "user",
                "content": TEXT_INTENT_PROMPT.format(question=question)
            }
        ],
        temperature=0
    )

    raw = response.choices[0].message.content

    # extract JSON
    text = re.sub(r"```json", "", raw, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("❌ No JSON object found")

    json_text = match.group()

    # DEBUG 2 — extracted JSON text
    raw_intent = json.loads(json_text)

    # 🔥 HARD NORMALIZATION (CRITICAL)
    intent = {}
    for k, v in raw_intent.items():
        clean_key = k.replace('"', "").strip()
        intent[clean_key] = v

    # ✅ CONVERT TABLE TO DIMENSIONS
    table_name = intent.get("table", "")
    
    # Handle 2D tables (e.g., "industry_x_practice_area")
    if "_x_" in table_name:
        dims = table_name.split("_x_")
        intent["dimensions"] = [d.strip() for d in dims]
    # Handle 1D tables
    else:
        intent["dimensions"] = [table_name] if table_name else []
    
    # Rename filters to filter_values for consistency
    if "filters" in intent:
        intent["filter_values"] = intent.pop("filters")
    

    return intent
