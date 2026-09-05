from typing import Callable, List, Tuple, Any, Optional

from dataclasses import dataclass, field

import json

import os

DB_PATH = os.path.join(os.path.dirname(__file__), "users.json")

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

def login():
    for atte in range(4,-1,-1):
        print("enter your user name")
        username = input(">")
        print("enter your password")
        password = input(">")

        stages = [
            ("check_user_exists", check_user_exists),
            ("check_password_match", check_password_match),
        ]

        login_data = {"username": username, "password": password}
        p = Pipeline(stages)
        result = p.run(login_data)
        if result.success:
            print("Login successful!")
            break
        else:
            print(f"Login failed check username or password .{atte} attempts left.")
    else:
        print("all attempt used")
def create_acc():
    print("enter your email")
    email=input(">")
    print("enter your username")
    username=input(">")
    print("enter your password")
    password=input(">")
    k=input("Keep these?(Y/n)").lower() or 'y'
    if k !='n':
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
            "username": username,
            "password": password,
            "email": email,
        }

        p = Pipeline(stages)
        result = p.run(signup_data)
        print(result)
    elif k=='n':
        create_acc()
def main():
    print("login or create a new account (L/c)")
    i=input(">").lower() or 'l'
    if i == "l":
        login()
    elif i=="c":
        create_acc()
if __name__ == "__main__":
    main()
    