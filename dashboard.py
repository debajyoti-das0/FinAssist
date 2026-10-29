import streamlit as st
import requests
import pandas as pd

# 1. Page configuration
st.set_page_config(
    page_title="FinAssist",
    page_icon="🏦",
    layout="wide"
)

st.title("🏦 FinAssist: Fraud & Risk Intelligence")


# 2. Reusable HTTP session
@st.cache_resource
def get_http_session():
    return requests.Session()


http_session = get_http_session()
API_URL = "http://localhost:8000/api/chat"


# 3. Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "How can I help you investigate today?",
            "data": None,
            "sql": None
        }
    ]


# 4. Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message.get("data"):
            st.dataframe(
                pd.DataFrame(message["data"]),
                use_container_width=True
            )

        if message.get("sql"):
            with st.expander("View Generated SQL"):
                st.code(message["sql"], language="sql")


# 5. Handle user input
if prompt := st.chat_input("Ask a question about fraud or risk..."):

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing database..."):

            try:
                response = http_session.post(
                    API_URL,
                    json={"question": prompt},
                    timeout=120
                )

                response.raise_for_status()
                result = response.json()

                summary = (
                    result.get("summary")
                    or "No response was returned by the backend."
                )

                data_payload = result.get("data_payload")
                generated_sql = result.get("generated_sql")

                # Display answer
                st.markdown(summary)

                # Display database results
                if data_payload:
                    st.dataframe(
                        pd.DataFrame(data_payload),
                        use_container_width=True
                    )
                elif data_payload is not None:
                    st.info("No matching database records were found.")

                # Display generated SQL
                if generated_sql:
                    with st.expander("View Generated SQL"):
                        st.code(generated_sql, language="sql")

                # Save assistant response
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": summary,
                    "data": data_payload,
                    "sql": generated_sql
                })

            except requests.exceptions.ConnectionError:
                error_message = (
                    "Cannot connect to the backend. "
                    "Please ensure the FastAPI server is running."
                )

                st.error(error_message)

            except requests.exceptions.Timeout:
                error_message = (
                    "The request timed out. Please try again."
                )

                st.error(error_message)

            except requests.exceptions.HTTPError as e:
                error_message = (
                    f"Backend returned an HTTP error: {e.response.status_code}"
                )

                st.error(error_message)

            except Exception:
                error_message = (
                    "An unexpected error occurred while processing your request."
                )

                st.error(error_message)