const API_BASE = "http://127.0.0.1:8000";

function showMessage(text, type) {
    const box = document.getElementById("message-box");
    box.innerHTML = `<div class="message ${type}">${text}</div>`;
}

function clearMessage() {
    document.getElementById("message-box").innerHTML = "";
    }

    document.getElementById("login-btn").addEventListener("click", handleLogin);

async function handleLogin() {
    clearMessage();
    const email = document.getElementById("login-email").value.trim();
    const password = document.getElementById("login-password").value;

    if (!email || !password) {
        showMessage("Enter your email and password.", "error");
        return;
    }
    if (!email.includes("@") || !email.includes(".")) {
        showMessage("Please enter a valid email address.", "error");
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
        });
        const data = await res.json();

        if (!res.ok) {
        showMessage(data.detail || "Something went wrong.", "error");
        return;
        }

        if (data.access_token) {
        localStorage.setItem("access_token", data.access_token);
        showMessage("Signed in. (Dashboard coming in the next phase.)", "success");
        } else {
        showMessage(data.detail, "success");
        }
    } catch (err) {
        showMessage("Could not reach the server.", "error");
    }
    }
document.querySelectorAll(".tab").forEach(tab => {
    tab.addEventListener("click", () => {
        document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
        tab.classList.add("active");
        clearMessage();

        document.getElementById("login-step-1").classList.add("hidden");
        document.getElementById("register-step-1").classList.add("hidden");

        if (tab.dataset.tab === "login") {
        document.getElementById("login-step-1").classList.remove("hidden");
        } else {
        document.getElementById("register-step-1").classList.remove("hidden");
        }
    });
});

document.getElementById("register-btn").addEventListener("click", handleRegister);

async function handleRegister() {
    clearMessage();
    const full_name = document.getElementById("register-name").value.trim();
    const email = document.getElementById("register-email").value.trim();
    const password = document.getElementById("register-password").value;

    if (!full_name || !email || !password) {
        showMessage("Fill in all fields.", "error");
        return;
    }
    if (!email.includes("@") || !email.includes(".")) {
        showMessage("Please enter a valid email address.", "error");
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ full_name, email, password }),
        });
        const data = await res.json();

        if (!res.ok) {
        showMessage(data.detail || "Something went wrong.", "error");
        return;
        }

        showMessage("Account created! Check your email for a verification code.", "success");
    } catch (err) {
        showMessage("Could not reach the server.", "error");
    }
}