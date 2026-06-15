import html as _html
import io
from datetime import datetime

import openai
import pandas as pd
import streamlit as st
from openai import OpenAI

# Fix #9: constant at module level, not mid-script
MAX_BYTES = 200 * 1024

st.set_page_config(page_title="CSV Analyzer", layout="centered")

st.markdown(
    """
    <style>
    /* ── Base ── */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background-color: #ffffff;
        color: #1a1a1a;
        font-family: "Inter", "Segoe UI", system-ui, sans-serif;
    }

    /* ── Remove default Streamlit chrome ── */
    #MainMenu, footer, header { visibility: hidden; }
    [data-testid="stDecoration"] { display: none; }

    /* ── App header bar ── */
    .app-header {
        border-bottom: 1px solid #e0e0e0;
        padding-bottom: 14px;
        margin-bottom: 28px;
    }
    .app-header h1 {
        font-size: 1.25rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        color: #111111;
        margin: 0;
    }
    .app-header p {
        font-size: 0.8rem;
        color: #6b7280;
        margin: 3px 0 0 0;
    }

    /* ── Section labels ── */
    .section-label {
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.07em;
        text-transform: uppercase;
        color: #6b7280;
        margin-bottom: 6px;
    }

    /* ── Streamlit widget label overrides ── */
    .stTextInput > label,
    .stFileUploader > label,
    .stTextArea > label {
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        color: #374151 !important;
        letter-spacing: 0.01em;
    }

    /* ── Inputs ── */
    .stTextInput input,
    .stTextArea textarea {
        background-color: #f9fafb !important;
        border: 1px solid #d1d5db !important;
        border-radius: 6px !important;
        color: #111111 !important;
        font-size: 0.875rem !important;
    }
    .stTextInput input:focus,
    .stTextArea textarea:focus {
        border-color: #374151 !important;
        box-shadow: 0 0 0 2px rgba(55,65,81,0.12) !important;
    }

    /* ── File uploader ── */
    [data-testid="stFileUploader"] section {
        background-color: #f9fafb !important;
        border: 1px dashed #d1d5db !important;
        border-radius: 6px !important;
    }

    /* ── Primary button ── */
    .stButton > button[kind="primary"] {
        background-color: #111827 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.04em !important;
        text-transform: uppercase !important;
        padding: 0.5rem 1.4rem !important;
        transition: background-color 0.15s ease !important;
    }
    .stButton > button[kind="primary"]:hover:not(:disabled) {
        background-color: #1f2937 !important;
    }
    .stButton > button[kind="primary"]:disabled {
        background-color: #9ca3af !important;
        cursor: not-allowed !important;
    }

    /* ── Dataset preview table ── */
    [data-testid="stDataFrame"] {
        border: 1px solid #e5e7eb;
        border-radius: 6px;
        overflow: hidden;
    }

    /* ── Results card ── */
    .results-card {
        background-color: #f9fafb;
        border: 1px solid #e5e7eb;
        border-left: 3px solid #111827;
        border-radius: 6px;
        padding: 20px 24px;
        margin-top: 8px;
    }
    .results-meta {
        font-size: 0.72rem;
        color: #9ca3af;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-bottom: 12px;
        display: flex;
        gap: 16px;
    }
    .results-body {
        font-size: 0.875rem;
        color: #1a1a1a;
        line-height: 1.65;
    }
    .results-body p { margin: 0 0 0.6em 0; }
    .results-body ul, .results-body ol { padding-left: 1.2em; }

    /* ── Divider ── */
    hr {
        border: none;
        border-top: 1px solid #e5e7eb;
        margin: 24px 0;
    }

    /* ── Status / alert overrides ── */
    [data-testid="stAlert"] {
        border-radius: 6px !important;
        font-size: 0.85rem !important;
    }

    /* ── Caption / meta text ── */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #9ca3af !important;
        font-size: 0.75rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Header ──────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="app-header">
        <h1>CSV Analyzer</h1>
        <p>Upload a dataset, ask a question, and get instant insights.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Configuration ────────────────────────────────────────────────────────────
api_key = st.text_input(
    "API Key",
    type="password",
    placeholder="Enter your API key",
    help="Used only for this session. Never stored or logged.",
)

st.divider()

# ── File Upload ──────────────────────────────────────────────────────────────
# Fix #10: removed redundant label_visibility="visible" (it is the default)
uploaded_file = st.file_uploader(
    "Dataset",
    type=["csv"],
    help="CSV files up to 200 KB.",
)

# Fix #4: cache parsed DataFrame in session_state so it is not re-parsed on
# every keystroke rerender — keyed by filename so switching files still works
df = None

if uploaded_file is not None:
    if st.session_state.get("file_name") != uploaded_file.name:
        raw = uploaded_file.getvalue()
        if len(raw) > MAX_BYTES:
            st.error(
                f"File size ({len(raw) / 1024:.1f} KB) exceeds the 200 KB limit. "
                "Upload a smaller file to continue."
            )
            st.session_state.df = None
            st.session_state.raw_len = 0
        else:
            try:
                parsed = pd.read_csv(io.BytesIO(raw))
                if parsed.empty:
                    st.warning("The uploaded file contains no data rows.")
                    st.session_state.df = None
                    st.session_state.raw_len = 0
                else:
                    st.session_state.df = parsed
                    st.session_state.raw_len = len(raw)
            except Exception:
                # Fix #3: don't leak the raw pandas exception message
                st.error("Could not read file. Make sure it is a valid CSV.")
                st.session_state.df = None
                st.session_state.raw_len = 0
        st.session_state.file_name = uploaded_file.name

    df = st.session_state.get("df")
    raw_len = st.session_state.get("raw_len", 0)

    if df is not None:
        st.markdown('<p class="section-label">Preview — first 5 rows</p>', unsafe_allow_html=True)
        st.dataframe(df.head(5), use_container_width=True)
        st.caption(f"{len(df):,} rows · {len(df.columns)} columns · {raw_len / 1024:.1f} KB")

# ── Query ────────────────────────────────────────────────────────────────────
if df is not None:
    st.divider()

    # Fix #5: cap question length to prevent runaway token usage
    question = st.text_input(
        "Question",
        placeholder="e.g. Which product had the highest sales last quarter?",
        max_chars=500,
    )

    run_clicked = st.button(
        "Run Analysis",
        disabled=not question.strip() or not api_key.strip(),
        type="primary",
    )

    if run_clicked:
        csv_text = df.to_csv(index=False)
        prompt = (
            "You are a data analyst. The user has provided a CSV dataset and a question. "
            "Answer the question accurately and concisely based solely on the data below.\n\n"
            f"CSV Data:\n{csv_text}\n\n"
            f"Question: {question}"
        )

        # Fix #6: use typed OpenAI exceptions instead of string matching
        try:
            client = OpenAI(api_key=api_key.strip())
            with st.spinner("Running analysis…"):
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a helpful data analyst. "
                                "Answer questions about CSV data clearly and accurately."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=1024,
                    temperature=0.1,
                )

            # Fix #7: guard against empty choices list before indexing
            if not response.choices:
                st.error("No result was returned. The request may have been filtered.")
            else:
                answer = response.choices[0].message.content
                timestamp = datetime.now().strftime("%d %b %Y · %H:%M")

                # Fix #1 + #8: HTML-escape both user input and model output
                # before injecting into an unsafe_allow_html block, then
                # replace newlines with <br> after escaping (not inside the
                # f-string, avoiding the chr(10) workaround)
                safe_q = _html.escape(question)
                safe_a = _html.escape(answer).replace("\n", "<br>")

                st.markdown('<p class="section-label">Results</p>', unsafe_allow_html=True)
                st.markdown(
                    f"""
                    <div class="results-card">
                        <div class="results-meta">
                            <span>Query: {safe_q}</span>
                            <span>{timestamp}</span>
                        </div>
                        <div class="results-body">{safe_a}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        except openai.AuthenticationError:
            st.error("Authentication failed. Check your API key and try again.")
        except openai.RateLimitError:
            st.error("Request limit reached. Wait a moment and try again.")
        except openai.BadRequestError as exc:
            if "context_length" in str(exc).lower():
                st.error("Dataset is too large to process. Try a smaller file or fewer columns.")
            else:
                st.error("The request was rejected. Check your inputs and try again.")
        except (openai.APIConnectionError, openai.APITimeoutError):
            st.error("Could not reach the service. Check your network connection and try again.")
        except openai.APIStatusError as exc:
            if "quota" in str(exc).lower():
                st.error("Usage limit reached. Check your account status and try again.")
            else:
                # Fix #2: never leak the raw SDK message to the user
                st.error("An unexpected error occurred. Please try again.")
        except Exception:
            st.error("An unexpected error occurred. Please try again.")
