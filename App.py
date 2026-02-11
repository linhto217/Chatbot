import json
import uuid
from datetime import datetime
from typing import List, Dict

import streamlit as st
from snowflake.snowpark.context import get_active_session

# ------------------------------------------
# Configuration
# ------------------------------------------
DEFAULT_SYSTEM_PROMPT = "Tu es un assistant utile."
HISTORY_TABLE = "CHATBOT"
FALLBACK_MODELS = [
    "claude-4-sonnet",
    "claude-3-7-sonnet",
    "claude-3-5-sonnet",
    "openai-gpt-4.1",
    "openai-o4-mini",
]

# ------------------------------------------
# Snowpark session
# ------------------------------------------
session = get_active_session()

# ------------------------------------------
# Fonctions utilitaires
# ------------------------------------------
def ensure_history_table(session):
    session.sql(f"""
        CREATE TABLE IF NOT EXISTS {HISTORY_TABLE} (
            conversation_id STRING,
            user_name STRING,
            timestamp TIMESTAMP_NTZ,
            role STRING,
            content STRING
        )
    """).collect()


def get_current_user(session) -> str:
    rows = session.sql("SELECT CURRENT_USER() AS user_name").collect()
    return str(rows[0]["USER_NAME"]) if rows else "UNKNOWN_USER"


def insert_message(session, conversation_id, user_name, role, content):
    session.sql(f"""
        INSERT INTO {HISTORY_TABLE} (conversation_id, user_name, timestamp, role, content)
        VALUES (?, ?, CURRENT_TIMESTAMP(), ?, ?)
    """, params=[conversation_id, user_name, role, content]).collect()


def load_conversation(session, conversation_id, user_name) -> List[Dict[str, str]]:
    rows = session.sql(f"""
        SELECT role, content
        FROM {HISTORY_TABLE}
        WHERE conversation_id = ?
          AND user_name = ?
        ORDER BY timestamp ASC
    """, params=[conversation_id, user_name]).collect()
    messages = [{"role": row["ROLE"].lower(), "content": row["CONTENT"]} for row in rows]
    if messages and messages[0]["role"] != "system":
        messages.insert(0, {"role": "system", "content": DEFAULT_SYSTEM_PROMPT})
    return messages

def parse_cortex_response_with_model(raw_response) -> str:
    """
    Parse la réponse Cortex et retourne uniquement le texte généré.
    """
    try:
        if hasattr(raw_response, "as_dict"):
            raw_response = raw_response.as_dict()

        if isinstance(raw_response, str):
            try:
                raw_response = json.loads(raw_response)
            except Exception:
                return raw_response.strip()

        if isinstance(raw_response, dict):
            choices = raw_response.get("choices", [])
            message_text = ""

            if choices:
                first = choices[0]
                if isinstance(first, dict):
                    msg = first.get("messages") or first.get("text") or ""
                    if isinstance(msg, list):
                        message_text = " ".join(str(m) for m in msg)
                    else:
                        message_text = str(msg)
                else:
                    message_text = str(first)

            return message_text.strip()

    except Exception as e:
        return f"Erreur de parsing: {str(e)}"

    return "Aucune réponse récupérable."



def call_cortex(session, model: str, history: List[Dict[str, str]], temperature: float) -> str:
    options = {"temperature": min(max(temperature, 0.0), 1.0)}
    rows = session.sql("""
        SELECT SNOWFLAKE.CORTEX.TRY_COMPLETE(
            ?,
            PARSE_JSON(?),
            PARSE_JSON(?)
        ) AS RESPONSE
    """, params=[model, json.dumps(history), json.dumps(options)]).collect()

    raw_response = rows[0]["RESPONSE"] if rows else None
    if not raw_response:
        return "Cortex n'a pas pu générer de réponse."

    # Return parsed text with model
    return parse_cortex_response_with_model(raw_response)


# ------------------------------------------
# Streamlit initialization
# ------------------------------------------
st.set_page_config(page_title="Chatbot Cortex - Snowflake")
st.title("Chatbot Cortex dans Snowflake")

ensure_history_table(session)
user_name = get_current_user(session)

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": DEFAULT_SYSTEM_PROMPT}]
if "model" not in st.session_state:
    st.session_state.model = FALLBACK_MODELS[0]
if "temperature" not in st.session_state:
    st.session_state.temperature = 0.2

# ------------------------------------------
# Sidebar
# ------------------------------------------
with st.sidebar:
    st.subheader("Paramètres")
    st.session_state.model = st.selectbox("Modèle Cortex", FALLBACK_MODELS, index=0)
    st.session_state.temperature = st.slider("Température", 0.0, 1.0, 0.2, 0.1)
    if st.button("Nouvelle conversation"):
        st.session_state.conversation_id = str(uuid.uuid4())
        st.session_state.messages = [{"role": "system", "content": DEFAULT_SYSTEM_PROMPT}]

# ------------------------------------------
# Display chat history
# ------------------------------------------
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ------------------------------------------
# User input
# ------------------------------------------
user_prompt = st.chat_input("Écrivez votre message...")
if user_prompt:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    insert_message(session, st.session_state.conversation_id, user_name, "user", user_prompt)

    # Call Cortex
    payload = st.session_state.messages.copy()
    with st.chat_message("assistant"):
        with st.spinner("Génération en cours..."):
            response = call_cortex(session, st.session_state.model, payload, st.session_state.temperature)
            st.markdown(response)

    # Add assistant message
    st.session_state.messages.append({"role": "assistant", "content": response})
    insert_message(session, st.session_state.conversation_id, user_name, "assistant", response)
