from typing import Callable, List, Tuple, Any, Optional

from dataclasses import dataclass, field

import json

import os

import streamlit as st

DB_PATH = os.path.join(os.path.dirname(__file__), "users.json")

FIELD_MAP = {
        "check_username": "username",
        "check_username_taken": "username",
        "check_password": "password",
        "check_email_format": "email",
        "check_email_taken": "email",
        "normalize_email": "email",
    }

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

def login_ui():
    st.title("Login")
    st.session_state.setdefault("login_attempts", 0)
    user = st.text_input("enter your username here:", placeholder="my user")
    password = st.text_input("enter your password here:", placeholder="password123", type="password")

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
            else:
                st.session_state.login_attempts += 1
                remaining = 5 - st.session_state.login_attempts
                st.error(f"{result.failed_reason} ({remaining} attempts left)")

def create_acc_ui():
    st.title("Sign Up")
    
    if st.session_state.get("signup_just_succeeded"):
        st.success("Account created!")
        st.session_state.signup_just_succeeded = False

    user = st.text_input("Username:", placeholder="enter your username here")
    if st.session_state.get("signup_failed_field") == "username":
        st.caption(f":red[{st.session_state.get('signup_failed_reason')}]")

    password = st.text_input("Password:", placeholder="enter your password here:", type="password")
    if st.session_state.get("signup_failed_field") == "password":
        st.caption(f":red[{st.session_state.get('signup_failed_reason')}]")

    email = st.text_input("Email", placeholder="enter your email here:")
    if st.session_state.get("signup_failed_field") == "email":
        st.caption(f":red[{st.session_state.get('signup_failed_reason')}]")

    if st.button("create account"):
        stages = [
                    ("check_username", check_username_len),
                    ("check_password", check_pass_len),
                    ("check_email_format", check_email),
                    ("normalize_email", nor_mail),
                    ("check_username_taken", name_not_taken),
                    ("check_email_taken", mail_not_taken),
                    ("create_account", create_account)
                ]
        
        signup_data = {
                    "username": user,
                    "password": password,
                    "email": email,
                }
        
        p = Pipeline(stages)
        result = p.run(signup_data)
        if result.success:
            st.session_state.signup_just_succeeded  = True
            st.session_state.signup_failed_field = None
            st.session_state.signup_failed_reason = None
        else:
            st.session_state.signup_failed_field = FIELD_MAP.get(result.failed_stage)
            st.session_state.signup_failed_reason = result.failed_reason
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

def main():
    st.set_page_config(page_title="Auth", page_icon=":lock:")
    st.markdown(AUTH_CSS, unsafe_allow_html=True)
    st.markdown(BUTTON_CSS,unsafe_allow_html=True)
    mode=mode_selector()
    if mode == "Login":
        login_ui()
    else:
        create_acc_ui()

if __name__ == "__main__":
    main()