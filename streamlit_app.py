import streamlit as st

from data_loader import load_all_tables, load_all_2d_tables
from chatbot import get_chatbot_client
from intent_parser import parse_intent
from llm_text_intent import llm_parse_text_intent
from text_answers import generate_text_answer, generate_2d_text_answer
from visualizations import plot_generic
from utils import resolve_measure_column

DEBUG = True

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="LegalVIEW Analytics Chatbot",
    layout="wide"
)

st.title("📊 LegalVIEW Dynamic Insights Chatbot")
st.caption("• LLM-powered insights • 1D & 2D pivots • Jun / Sep comparison ready")

# ---------------- SESSION STATE ----------------
if "version" not in st.session_state:
    st.session_state.version = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "DATA_1D" not in st.session_state:
    st.session_state.DATA_1D = None

if "DATA_2D" not in st.session_state:
    st.session_state.DATA_2D = None

# ---------------- LOAD CLIENT ----------------
@st.cache_resource
def get_client():
    return get_chatbot_client()

client = get_client()

# ---------------- VERSION SELECTION ----------------
st.markdown("### 📅 Choose Data Version")

col1, col2 = st.columns(2)

with col1:
    if st.button("📘 Jun", use_container_width=True):
        st.session_state.version = "Jun"
        st.session_state.DATA_1D = load_all_tables("Jun")
        st.session_state.DATA_2D = load_all_2d_tables("Jun")
        st.session_state.messages = []

with col2:
    if st.button("📙 Sep", use_container_width=True):
        st.session_state.version = "Sep"
        st.session_state.DATA_1D = load_all_tables("Sep")
        st.session_state.DATA_2D = load_all_2d_tables("Sep")
        st.session_state.messages = []

if not st.session_state.version:
    st.info("Please select a data version to start.")
    st.stop()

st.success(f"✅ Using {st.session_state.version} data")

DATA_1D = st.session_state.DATA_1D
DATA_2D = st.session_state.DATA_2D
version = st.session_state.version

# ---------------- CHAT HISTORY ----------------
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        if msg["type"] == "text":
            st.markdown(msg["content"])
        elif msg["type"] == "plot":
            # Add unique key based on message index
            st.plotly_chart(msg["content"], use_container_width=True, key=f"plot_history_{idx}")

# ---------------- USER INPUT ----------------
query = st.chat_input("Ask about rates, counts, trends, or visuals…")

if query:
    # ---- show user message ----
    st.session_state.messages.append(
        {"role": "user", "type": "text", "content": query}
    )

    with st.chat_message("user"):
        st.markdown(query)

    # ---------------- RULE-BASED (VISUAL) ----------------
    rule = parse_intent(query)

    if rule["chart"]:
        dims = rule.get("dimensions", [])

        if len(dims) == 1:
            df = DATA_1D.get(dims[0])
            if df is None:
                msg = f"⚠️ 1D table `{dims[0]}` not available."
            else:
                measure_col = resolve_measure_column(df, rule["year"], rule["metric"], version)
                if not measure_col:
                    msg = f"⚠️ Measure column not found for {rule['year']} {rule['metric']}."
                else:
                    try:
                        msg = plot_generic(df, measure_col, rule["chart"])
                    except ValueError as e:
                        msg = f"⚠️ Visualization error: {str(e)}"

        elif len(dims) == 2:
            # Try both possible 2D table key formats
            key1 = "_x_".join(dims)
            key2 = "_x_".join(reversed(dims))
            
            df = DATA_2D.get(key1)
            if df is None:
                df = DATA_2D.get(key2)
            
            if df is None:
                msg = f"⚠️ 2D table `{key1}` not available."
            else:
                measure_col = resolve_measure_column(df, rule["year"], rule["metric"], version)
                if not measure_col:
                    msg = f"⚠️ Measure column not found for {rule['year']} {rule['metric']}."
                else:
                    try:
                        msg = plot_generic(df, measure_col, rule["chart"])
                    except ValueError as e:
                        msg = f"⚠️ Visualization error: {str(e)}"

        else:
            msg = f"⚠️ Detected {len(dims)} dimensions. Expected 1 or 2."

        with st.chat_message("assistant"):
            if isinstance(msg, str):
                st.warning(msg)
            else:
                # Add unique key based on current message count
                st.plotly_chart(msg, use_container_width=True, key=f"plot_new_{len(st.session_state.messages)}")

        st.session_state.messages.append(
            {"role": "assistant", "type": "plot" if not isinstance(msg, str) else "text", "content": msg}
        )

    # ---------------- LLM TEXT ANSWER ----------------
    else:
        try:
            intent = llm_parse_text_intent(client, query)

            dims = intent.get("dimensions", [])

            # -------- 1D TEXT --------
            if len(dims) == 1:
                df = DATA_1D.get(dims[0])

                if df is None:
                    answer = f"⚠️ 1D table `{dims[0]}` not available."
                else:
                    answer = generate_text_answer(df, intent, version)

            # -------- 2D TEXT --------
            elif len(dims) == 2:
                # Try both possible key orders
                key1 = "_x_".join(dims)
                key2 = "_x_".join(reversed(dims))
                
                df = DATA_2D.get(key1)
                if df is None:
                    df = DATA_2D.get(key2)

                if df is None:
                    answer = f"⚠️ 2D table for `{' × '.join(dims)}` is not available."
                else:
                    answer = generate_2d_text_answer(df, intent, version)

            else:
                answer = f"⚠️ Detected {len(dims)} dimensions. Expected 1 or 2."

            with st.chat_message("assistant"):
                st.markdown(answer)

            st.session_state.messages.append(
                {"role": "assistant", "type": "text", "content": answer}
            )

        except Exception as e:
            error_msg = f"⚠️ Error: {type(e).__name__}: {str(e)}"

            if DEBUG:
                st.exception(e)

            with st.chat_message("assistant"):
                st.error(error_msg)

            st.session_state.messages.append(
                {"role": "assistant", "type": "text", "content": error_msg}
            )