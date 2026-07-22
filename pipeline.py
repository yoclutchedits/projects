from typing import Callable, List, Tuple, Any, Optional
from dataclasses import dataclass, field
from database import database_user,database_mail
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
    return(False,"username must be at least 8 charaters and include a number")
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
    if pw not in database_mail:
        return(True,None)
    return(False,"email already taken")
def name_not_taken(data):
    pw=data['username']
    if  pw not in database_user:
        return(True,None)
    return(False,"email already taken")
def create_account(data):
    return {**data, "status": "account created"}
def main():
    print("enter your email name")
    email=input(">")
    print("enter your user name")
    username=input(">")
    print("enter your password name")
    password=input(">")
    stages = [
        ("check_username", check_username_len),
        ("check_password", check_pass_len),
        ("check_email_format", check_email),
        ("normalize_email", nor_mail),
        ("check_username_taken", name_not_taken),
        ("check_email_taken", mail_not_taken),
        ("create_account", create_account),
    ]

    signup_data = {
        "username": username,
        "password": password,
        "email": email,
    }

    p = Pipeline(stages)
    result = p.run(signup_data)
    print(result)
if __name__ == "__main__":
    main()
    