import smtplib
from email.mime.text import MIMEText
import random
from keys import gogle as GMAIL_APP_PASSWORD
from keys import hf_key, g_key
from typing import Callable, List, Tuple, Any, Optional
from dataclasses import dataclass, field
import json
import io
from io import BytesIO
from openai import OpenAI
from huggingface_hub import InferenceClient
import requests
import os
import streamlit as st
import time
from streamlit_autorefresh import st_autorefresh
DB_PATH = os.path.join(os.path.dirname(__file__), "users.json")
GMAIL_ADDRESS = "x.prashanna.x@gmail.com"
FIELD_MAP = {
        "check_username": "username",
        "check_username_taken": "username",
        "check_password": "password",
        "check_email_format": "email",
        "check_email_taken": "email",
        "normalize_email": "email",
    }

CHAT_CSS = """
<style>
:root {
    color-scheme: light dark;
}
[data-testid="stSidebar"] {
    background-color: light-dark(#f8f9fa, #1f2937);
}
.history-wrap {
    max-height: 65vh; 
    overflow-y: auto; 
    padding-right: 4px;
}
.qa-card {
    border: 1px solid light-dark(#e2e8f0, #374151);
    background: light-dark(#ffffff, #111827);
    border-radius: 8px;
    padding: 12px;
    margin: 12px 0;
    box-shadow: 0 1px 3px light-dark(rgba(0,0,0,0.05), rgba(0,0,0,0.3));
}
.q {
    font-weight: 600; 
    color: light-dark(#1e3a8a, #93c5fd); 
    margin-bottom: 6px;
    font-size: 0.9rem;
}
.a {
    white-space: pre-wrap; 
    color: light-dark(#4a5568, #d1d5db); 
    line-height: 1.4;
    font-size: 0.85rem;
}
.meta {
    float: right;
    font-size: 0.75rem;
    opacity: 0.7;
    background: light-dark(#edf2f7, #2d3748);
    padding: 2px 6px;
    border-radius: 4px;
}
</style>
"""

BUTTON_CSS = """
<style>
.mode-btn button {
    border-radius: 20px;
    padding: 8px 20px;
    transition: all 0.15s ease;
    border: 1px solid light-dark(#e2e8f0, #374151);
}
.mode-btn button:hover {
    transform: scale(1.05);
    border-color: #3b82f6;
}
.mode-btn-active button {
    background-color: #3b82f6 !important;
    color: white !important;
    border-color: #3b82f6 !important;
}
</style>
"""


AUTH_CSS = """
<style>
:root {
    color-scheme: light dark;
}
[data-testid="stSidebar"] {
    background-color: light-dark(#f8f9fa, #1f2937);
}
.auth-card {
    border: 1px solid light-dark(#e2e8f0, #374151);
    background: light-dark(#ffffff, #111827);
    border-radius: 8px;
    padding: 20px;
    margin: 16px 0;
    box-shadow: 0 1px 3px light-dark(rgba(0,0,0,0.05), rgba(0,0,0,0.3));
}
.auth-title {
    font-weight: 600;
    color: light-dark(#1e3a8a, #93c5fd);
    font-size: 1.1rem;
    margin-bottom: 10px;
}
.attempts-left {
    font-size: 0.85rem;
    opacity: 0.75;
    color: light-dark(#b91c1c, #f87171);
}
.confirm-box {
    border: 1px dashed light-dark(#cbd5e1, #4b5563);
    border-radius: 6px;
    padding: 12px;
    margin: 10px 0;
    font-size: 0.85rem;
    white-space: pre-wrap;
}
</style>
"""

MATH_SYSTEM = """You are a Math Mastermind.
Solve with clear step-by-step reasoning, correct notation, and a final answer.
Verify when possible; mention an alternative method briefly if relevant."""

def generate_otp():
    code = random.randint(100000, 999999)
    return str(code)

def mode_selector():
    st.session_state.setdefault("mode", "Login")
    col1, col2 = st.columns(2)
    
    with col1:
        login_class = "mode-btn-active" if st.session_state.mode == "Login" else "mode-btn"
        st.markdown(f'<div class="{login_class}">', unsafe_allow_html=True)
        if st.button("🔑 Login", key="btn_login", use_container_width=True):
            st.session_state.mode = "Login"
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        signup_class = "mode-btn-active" if st.session_state.mode == "Sign Up" else "mode-btn"
        st.markdown(f'<div class="{signup_class}">', unsafe_allow_html=True)
        if st.button("✨ Sign Up", key="btn_signup", use_container_width=True):
            st.session_state.mode = "Sign Up"
        st.markdown('</div>', unsafe_allow_html=True)
    return st.session_state.mode

def send_otp_email(to_address, code):
    msg = MIMEText(f"Your verification code is: {code}")
    msg["Subject"] = "Your verification code"
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = to_address

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, to_address, msg.as_string())

def login_ui():
    st.title("Login")
    st.session_state.setdefault("login_attempts", 0)
    user = st.text_input("username:", placeholder="enter your username here:")
    password = st.text_input("password:", placeholder="enter your password here:", type="password")

    if st.button("Log in"):
        if st.session_state.login_attempts >= 5:
            st.error("Too many failed attempts. Try again later.")
        else:
            stages = [
                ("check_user_exists", check_user_exists),
                ("check_password_match", check_password_match),
            ]
            login_data = {"username": user, "password": password}
            p = Pipeline(stages)
            result = p.run(login_data)
            if result.success:
                st.success("Login successful!")
                st.session_state.login_attempts = 0
                st.session_state.authenticated = True
                st.session_state.current_user = user
                st.rerun()
            else:
                st.session_state.login_attempts += 1
                remaining = 5 - st.session_state.login_attempts
                st.error(f"{result.failed_reason} ({remaining} attempts left)")

def create_acc_ui():
    st.title("Sign Up")
    st.session_state.setdefault("otp_stage", "form")
    st.session_state.setdefault("otp_attempts", 5)

    if st.session_state.get("signup_just_succeeded"):
        st.success("Account created!")
        st.session_state.signup_just_succeeded = False

    if st.session_state.otp_stage == "form":
        user = st.text_input("Username:", placeholder="enter your username here")
        if st.session_state.get("signup_failed_field") == "username":
            st.caption(f":red[{st.session_state.get('signup_failed_reason')}]")

        password = st.text_input("Password:", placeholder="enter your password here:", type="password")
        if st.session_state.get("signup_failed_field") == "password":
            st.caption(f":red[{st.session_state.get('signup_failed_reason')}]")

        email = st.text_input("Email", placeholder="enter your email here:")
        if st.session_state.get("signup_failed_field") == "email":
            st.caption(f":red[{st.session_state.get('signup_failed_reason')}]")

        if st.button("Send Code"):
            stages = [
                ("check_username", check_username_len),
                ("check_password", check_pass_len),
                ("check_email_format", check_email),
                ("normalize_email", nor_mail),
                ("check_username_taken", name_not_taken),
                ("check_email_taken", mail_not_taken),
            ]
            signup_data = {"username": user, "password": password, "email": email}
            p = Pipeline(stages)
            result = p.run(signup_data)

            if result.success:
                code = generate_otp()
                st.session_state.pending_otp = code
                st.session_state.pending_signup_data = result.final_value
                send_otp_email(result.final_value["email"], code)
                st.session_state.otp_stage = "verify"
                st.session_state.otp_attempts = 5
                st.session_state.otp_last_sent = time.time()
                st.session_state.signup_failed_field = None
                st.session_state.signup_failed_reason = None
            else:
                st.session_state.signup_failed_field = FIELD_MAP.get(result.failed_stage)
                st.session_state.signup_failed_reason = result.failed_reason
            st.rerun()

    elif st.session_state.otp_stage == "verify":
        st_autorefresh(interval=1000, key="otp_timer")
        email = st.session_state.pending_signup_data["email"]
        st.write(f"Enter the code sent to {email}")
        entered_code = st.text_input("Verification code")
        col1,col2,col3=st.columns(3)
        with col1:
            if st.button("Confirm"):
                if st.session_state.otp_attempts <= 0:
                    st.error("Too many incorrect attempts.")
                elif entered_code == st.session_state.pending_otp:
                    create_account(st.session_state.pending_signup_data)
                    st.session_state.otp_stage = "form"
                    st.session_state.signup_just_succeeded = True
                    st.session_state.pending_otp = None
                    st.session_state.pending_signup_data = None
                    st.rerun()
                else:
                    st.session_state.otp_attempts -= 1
                    st.error(f"Incorrect code. {st.session_state.otp_attempts} attempts left.")
        with col2:
            if st.button("Start Over"):
                st.session_state.otp_stage = "form"
                st.session_state.pending_otp = None
                st.session_state.pending_signup_data = None
                st.session_state.otp_attempts = 5
                st.rerun()
        with col3:
            seconds_since_last_send = time.time() - st.session_state.get("otp_last_sent", 0)
            cooldown_remaining = 60 - seconds_since_last_send
            if cooldown_remaining > 0:
                st.button(f"Resend ({int(cooldown_remaining)}s)", disabled=True)
            else:
                if st.button("Resend Code"):
                    new_code = generate_otp()
                    st.session_state.pending_otp = new_code
                    send_otp_email(st.session_state.pending_signup_data["email"], new_code)
                    st.session_state.otp_attempts = 5
                    st.session_state.otp_last_sent = time.time()
                    st.rerun()

def load_db():
    with open(DB_PATH, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DB_PATH, "w") as f:
        json.dump(db, f, indent=2)
@dataclass
class PipelineResult:
    success: bool
    final_value: Any
    failed_stage: Optional[str] = None
    failed_reason: Optional[str] = None
    trace: List[str] = field(default_factory=list)

class Pipeline:
    def __init__(self, stages: List[Tuple[str, Callable]]):
        self.stages = stages
    def run(self, initial_value: Any) -> PipelineResult:
        value = initial_value
        trace = []
        for name, fn in self.stages:
            trace.append(name)
            try:
                result = fn(value)
            except Exception as e:
                return PipelineResult(success=False, final_value=value,failed_stage=name, failed_reason=str(e), trace=trace)
            is_validator = isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], bool)
            if is_validator:
                ok, reason = result
                if not ok:
                    return PipelineResult(success=False, final_value=value,failed_stage=name, failed_reason=reason, trace=trace)
            else:
                value = result
        return PipelineResult(success=True, final_value=value, trace=trace)

def check_username_len(data):
    if len(data['username']) >=3:
        return(True,None)
    return(False,"username must be at least 3 charaters")

def check_pass_len(data):
    pw=data['password']
    if len(pw) >=8 and any(c.isdigit() for c in pw):
        return(True,None)
    return(False,"password must be at least 8 charaters and include a number")

def check_email(data):
    pw=data['email']
    if "@" in pw and "." in pw:
        return(True,None)
    return(False,"invalid email format")

def nor_mail(data):
    data['email'] = data['email'].lower()
    
    return data
def mail_not_taken(data):
    pw=data['email']
    db=load_db()
    if pw not in db['emails']:
        return(True,None)
    return(False,"email already taken")

def name_not_taken(data):
    pw=data['username']
    db=load_db()
    if  pw not in db['usernames']:
        return(True,None)
    return(False,"username already taken")

def create_account(data):
    db = load_db()
    db['usernames'].append(data['username'])
    db['emails'].append(data['email'])
    db['passwords'].append(data['password'])
    save_db(db)
    return {**data, "status": "account created"}

def check_user_exists(data):
    db = load_db()
    if data['username'] in db['usernames']:
        return (True, None)
    return (False, "no account with that username")

def check_password_match(data):
    db = load_db()
    idx = db['usernames'].index(data['username'])
    if db['passwords'][idx] == data['password']:
        return (True, None)
    return (False, "incorrect password")


GROQ_URL = "https://api.groq.com/openai/v1"

def hf(prompt: str, temperature: float = 0.3, max_tokens: int = 512) -> str:
    models = ["meta-llama/Llama-3.1-8B-Instruct"]
    key = hf_key
    if key is None:
        raise ValueError("API key not found. Please set 'hf_key' in the Streamlit secrets management dashboard.")
    
    last_error = None
    for m in models:
        try:
            c = InferenceClient(token=key)
            r = c.chat_completions(
                model=m,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return r.choices[0].message.content
        except Exception as e:
            last_error = e
            
    return f"HF model failed. Models tried: {models}. Error: {last_error}"

def groq(prompt: str, temperature: float = 0.3, max_tokens: int = 512) -> str:
    models = ["llama-3.1-8b-instant", "mixtral-8x7b-32768"]
    key = g_key
    if key is None:
        raise ValueError("API key not found. Please set 'g_key' in the Streamlit secrets management dashboard.")
    
    c = OpenAI(api_key=key, base_url=GROQ_URL)
    last_error = None
    for m in models:
        try:
            r = c.chat.completions.create(
                model=m,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return r.choices[0].message.content
        except Exception as e:
            last_error = e
            continue
    return f"Groq model failed. Models tried: {models}. Error: {last_error}"

def export_txt(history):
    text = "".join([f"Q{i}: {h['question']}\nA{i}: {h['answer']}\n\n" for i, h in enumerate(history, 1)])
    return io.BytesIO(text.encode('utf-8'))

def teaching_answer(generate_response, q: str) -> str:
    return generate_response(q, temperature=0.3, max_tokens=1024)

def math_ans(generate_response, q: str, level: str) -> str:
    prompt = f"{MATH_SYSTEM}\n\nProblem: ({level}) {q}\n\nAnswer:"
    return generate_response(prompt, temperature=0.3, max_tokens=1024)

def run_ai(generate_response):
    st.title("Teaching Assistant")
    st.session_state.setdefault("history_ata", [])
    with st.sidebar:
        st.write("---")
        st.write("Teaching Assistant History")
        c1, c2 = st.columns([1, 2])
        if c1.button("Clear History", key="clear_ata"):
            st.session_state.history_ata = []
            st.rerun()
        if st.session_state.history_ata:
            c2.download_button("Export History", data=export_txt(st.session_state.history_ata), file_name="history.txt", mime="text/plain", key="dl_ata")
    q = st.text_input("Enter your question here:", placeholder="e.g., Explain the Pythagorean theorem", key="q_ata")
    if st.button("Get Answer", key="btn_ata"):
        if not q.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("Generating answer..."):
                answer = teaching_answer(generate_response, q)
                st.session_state.history_ata.append({"question": q, "answer": answer})
                st.success("Answer generated!")
                st.rerun()
    if not st.session_state.history_ata:
        return
    st.markdown(CHAT_CSS, unsafe_allow_html=True)
    html = '<div class="history-wrap">'
    for i, h in enumerate(st.session_state.history_ata, 1):
        html += f'<div class="qa-card"><div class="q">Q{i}: {h["question"]}</div><div class="a">{h["answer"]}</div></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def run_math(generate_response):
    st.title("Math Problem Solver")
    st.session_state.setdefault("history_math", [])
    with st.sidebar:
        st.write("---")
        st.write("Math Problem Solver History")
        c1, c2 = st.columns([1, 2])
        if c1.button("Clear History", key="clear_math"):
            st.session_state.history_math = []
            st.rerun()
        if st.session_state.history_math:
            c2.download_button("Export History", data=export_txt(st.session_state.history_math), file_name="history.txt", mime="text/plain", key="dl_math")
    with st.form("math_form", clear_on_submit=True):
        q = st.text_area("Enter your math problem here:", placeholder="e.g., Solve for x in the equation 2x + 3 = 7", key="q_math", height=100)
        a, b = st.columns([3, 1])
        solve = a.form_submit_button("Solve", use_container_width=True)
        lvl = b.selectbox("Difficulty Level", ["Easy", "Medium", "Hard"], index=1)
        if solve:
            if not q.strip():
                st.warning("Please enter a math problem.")
            else:
                with st.spinner("Solving..."):
                    answer = math_ans(generate_response, q, lvl)
                    if "error" in answer.lower():
                        st.error(f"Error: {answer}")
                    else:
                        st.session_state.history_math.append({"question": q, "answer": answer, "level": lvl})
                        st.success("Problem solved!")
                        st.rerun()                    
    if not st.session_state.history_math:
        return
    st.markdown(CHAT_CSS, unsafe_allow_html=True)
    html = '<div class="history-wrap">'
    for i, h in enumerate(st.session_state.history_math, 1):
        item_lvl = h.get("level", "Medium")
        html += f'<div class="qa-card"><div class="q">Q{i}: {h["question"]}<span class="meta">{item_lvl}</span></div><div class="a">{h["answer"]}</div></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def safe_img_gen(generate_response):
    filter_url = "https://filters-zeta.vercel.app/api/filter"
    img_model = "stabilityai/stable-diffusion-3-medium-diffusers"
    hf_token = hf_key
    img_client = InferenceClient(provider='hf-inference', api_key=hf_token)
    st.title("Image Generation (Safe Mode)")
    if "generated_image" not in st.session_state:
        st.session_state.generated_image = None
    def is_safe_prompt(prompt: str):
        try:
            response = requests.post(filter_url, json={"prompt": prompt}, timeout=15)
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"): 
                    return True, None
                else:
                    return False, "Prompt flagged as unsafe by the filter."
            else:
                err_msg = f"Error checking prompt safety: {response.status_code}"
                return False, err_msg
        except Exception as e:
            return False, str(e)
    def generate_image(prompt: str):
        safe, error = is_safe_prompt(prompt)
        if not safe:
            return None, error
        try:
            img = img_client.text_to_image(model=img_model, prompt=prompt)
            return img, None
        except Exception as e:
            return None, str(e)
    with st.form("img_form", clear_on_submit=False):
        prompt = st.text_area("Enter your image prompt here:", placeholder="e.g., A serene landscape with mountains and a river at sunset", key="prompt_img", height=100)
        submit = st.form_submit_button("Generate Image")
        if submit:
            if not prompt.strip():
                st.warning("Please enter an image prompt.")
            else:
                with st.spinner("Generating image..."):
                    img, error = generate_image(prompt)
                    if img:
                        st.session_state.generated_image = img
                        st.success("Image generated successfully!")
                    else:
                        st.session_state.generated_image = None
                        st.error(f"Failed to generate image: {error}")
    with st.sidebar:
        st.write("---")
        st.write("Image Controls")
        c1, c2 = st.columns([1, 1])
        if c1.button("Clear Photo Image", key="clear_img_state"):
            st.session_state.generated_image = None
            st.rerun()
    if st.session_state.generated_image is not None:
        st.image(st.session_state.generated_image, caption="Generated Image", use_container_width=True)
        buffer = BytesIO()
        st.session_state.generated_image.save(buffer, format="PNG")
        c2.download_button(
            label="Download Image", 
            data=buffer.getvalue(), 
            file_name="generated_image.png", 
            mime="image/png",
            key="download_img_btn"
        )

def main():
    st.set_page_config(page_title="Auth", page_icon=":lock:")
    st.markdown(AUTH_CSS, unsafe_allow_html=True)
    st.markdown(BUTTON_CSS, unsafe_allow_html=True)
    st.session_state.setdefault("authenticated", False)
    
    if not st.session_state.authenticated:
        mode = mode_selector()
        if mode == "Login":
            login_ui()
        else:
            create_acc_ui()
    else:
        st.sidebar.title("AI Settings")
        if st.sidebar.button("Log Out"):
            st.session_state.authenticated = False
            st.rerun()
        st.sidebar.title("AI Settings")
        ai_engine = st.sidebar.radio("Select AI Engine:", ["Groq", "Hugging Face"], index=0, key="ai_engine")
        generate_response = groq if ai_engine == "Groq" else hf
        st.sidebar.write("---")
        st.sidebar.write("Choose a mode:")
        mode = st.sidebar.radio("", ["Teaching Assistant", "Math Problem Solver", "Image Generation"], key="app_mode")
        if mode == "Teaching Assistant":
            run_ai(generate_response)
        elif mode == "Math Problem Solver":
            run_math(generate_response)
        elif mode == "Image Generation":
            safe_img_gen(generate_response)
if __name__ == "__main__":
    main()