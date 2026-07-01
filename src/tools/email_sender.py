import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()


def email_sender(state: dict) -> dict:
    print("\n=== SEND_EMAIL_NODE DEBUG ===")

    sender       = os.getenv("GMAIL_ADDRESS")
    app_password = os.getenv("GMAIL_APP_PASSWORD")
    recipient    = os.getenv("NOTIFY_EMAIL", sender)

    print(f"DEBUG sender      : {sender}")
    print(f"DEBUG recipient   : {recipient}")
    print(f"DEBUG password set: {'YES' if app_password else 'NO'}")

    if not sender or not app_password:
        state["error"] = "GMAIL_ADDRESS or GMAIL_APP_PASSWORD missing from environment"
        print(f"❌ {state['error']}")
        state["email_sent"] = False
        return state

    risk_score   = state.get("risk_score", "UNKNOWN")
    risk_factors = state.get("risk_factors", [])
    pr_url       = state.get("pr_url", "N/A")
    comment_url  = state.get("comment_url", "N/A")
    repo         = state.get("repo_full_name", "N/A")
    pr_number    = state.get("pr_number", "N/A")

    subject = f"[ChangeGuard] HIGH RISK PR — {repo} #{pr_number}"

    factors_text = "\n".join(f"  - {f}" for f in risk_factors)

    text_body = f"""
CHANGEGUARD AI — HIGH RISK PR DETECTED

Repo: {repo}
PR #: {pr_number}
PR Link: {pr_url}

Risk Score: {risk_score}

Risk Factors:
{factors_text}

{state.get('threat_report', '')}

GitHub Comment: {comment_url}
    """.strip()

    html_body = f"""
<html><body style="font-family: monospace; padding: 20px;">
  <h2 style="color: red;">🔴 ChangeGuard AI — HIGH RISK PR</h2>
  <p><b>Repo:</b> {repo}</p>
  <p><b>PR:</b> <a href="{pr_url}">#{pr_number}</a></p>
  <p><b>Risk Score:</b> {risk_score}</p>
  <hr/>
  <b>Github</b>
  <p>🔗 <b>GitHub Comment:</b> <a href="{comment_url}">{comment_url}</a></p>
  <hr/>
  <b>Risk Factors:</b>
  <ul>{''.join(f"<li>{f}</li>" for f in risk_factors)}</ul>
  <hr/>
  <pre>{state.get('threat_report', '')}</pre>
  <hr/>
  <small style="color: grey;">Sent automatically by ChangeGuard AI</small>
</body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["From"]    = sender
    msg["To"]      = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        print("DEBUG [1] Connecting to smtp.gmail.com:465 ...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            print("DEBUG [2] Connected ✓")
            server.login(sender, app_password)
            print("DEBUG [3] Logged in ✓")
            server.sendmail(sender, recipient, msg.as_string())
            print("DEBUG [4] sendmail() called ✓")

        state["email_sent"] = True
        print(f"✅ Email sent to: {recipient}")

    except smtplib.SMTPAuthenticationError:
        state["error"] = "AUTH FAILED — wrong app password or 2FA not enabled"
        print(f"❌ {state['error']}")
        state["email_sent"] = False

    except smtplib.SMTPConnectError:
        print("❌ CONNECT FAILED on port 465, trying 587 ...")
        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.ehlo()
                server.starttls()
                server.login(sender, app_password)
                server.sendmail(sender, recipient, msg.as_string())
            state["email_sent"] = True
            print(f"✅ Email sent (587) to: {recipient}")
        except Exception as e2:
            state["error"] = f"Port 587 also failed: {type(e2).__name__}: {e2}"
            print(f"❌ {state['error']}")
            state["email_sent"] = False

    except Exception as e:
        state["error"] = f"Unexpected error: {type(e).__name__}: {e}"
        print(f"❌ {state['error']}")
        state["email_sent"] = False

    print("=== END DEBUG ===\n")
    return state