import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.config import settings

logger = logging.getLogger("thinkfree.email")


class EmailService:
    @staticmethod
    def _send_smtp_payload(to_email: str, subject: str, html_body: str, text_body: Optional[str] = None) -> bool:
        """Synchronously send an email via Gmail SMTP using STARTTLS."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"ThinkFree <{settings.SMTP_FROM}>"
            msg["To"] = to_email

            if text_body:
                msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM, [to_email], msg.as_string())

            logger.info("Email dispatched successfully to %s: %s", to_email, subject)
            return True
        except Exception as e:
            logger.error("Failed to send email to %s via %s:%s - Error: %s", to_email, settings.SMTP_HOST, settings.SMTP_PORT, e)
            return False

    @classmethod
    async def send_password_reset_email(
        cls, to_email: str, reset_token: str, user_name: Optional[str] = None
    ) -> bool:
        """Send a password reset email asynchronously with a secure token link."""
        name = user_name or to_email.split("@")[0].title()
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        subject = "ThinkFree · Reset Your Account Password"

        plain_text = f"""Hello {name},

You requested a password reset for your ThinkFree account.
Click the link below or paste it into your browser to set a new password:
{reset_link}

This link is valid for 30 minutes. If you did not request this reset, you can safely ignore this email.

— The ThinkFree Team
"""

        html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Reset Your Password</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #07090e; color: #f1f5f9; margin: 0; padding: 40px 20px; }}
    .container {{ max-width: 560px; margin: 0 auto; background: #0c101b; border: 1px solid rgba(255,255,255,0.08); border-radius: 20px; padding: 36px; box-shadow: 0 20px 40px rgba(0,0,0,0.5); }}
    .logo {{ display: inline-block; font-weight: 800; font-size: 20px; color: #ffffff; letter-spacing: -0.5px; margin-bottom: 24px; }}
    .logo span {{ color: #6366f1; }}
    h1 {{ font-size: 22px; font-weight: 700; color: #ffffff; margin-top: 0; margin-bottom: 12px; }}
    p {{ font-size: 14px; line-height: 1.6; color: #94a3b8; margin: 0 0 20px 0; }}
    .btn-container {{ text-align: center; margin: 30px 0; }}
    .btn {{ display: inline-block; background: #6366f1; color: #ffffff !important; text-decoration: none; font-weight: 600; font-size: 14px; padding: 14px 32px; border-radius: 12px; box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4); }}
    .link-fallback {{ font-size: 11px; word-break: break-all; color: #64748b; background: rgba(255,255,255,0.02); padding: 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.04); font-family: monospace; }}
    .footer {{ margin-top: 32px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.06); font-size: 11px; color: #64748b; text-align: center; font-family: monospace; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="logo">Think<span>Free</span></div>
    <h1>Reset Your Password</h1>
    <p>Hello {name},</p>
    <p>We received a request to reset the password for your ThinkFree cognitive learning account. Click the button below to choose a new password:</p>
    
    <div class="btn-container">
      <a href="{reset_link}" class="btn" target="_blank">Reset Password →</a>
    </div>

    <p style="font-size: 12px; color: #64748b;">Or copy and paste this link into your browser:</p>
    <div class="link-fallback">{reset_link}</div>

    <p style="font-size: 12px; color: #64748b; margin-top: 24px;">
      This security link will expire in <strong>30 minutes</strong>. If you did not make this request, you can safely disregard this message; your account credentials remain secure.
    </p>

    <div class="footer">
      ThinkFree Cognitive Platform · Course Project F102 Group 68 · BITS Pilani
    </div>
  </div>
</body>
</html>"""

        return await asyncio.to_thread(cls._send_smtp_payload, to_email, subject, html_body, plain_text)

    @classmethod
    async def send_welcome_email(cls, to_email: str, user_name: str) -> bool:
        """Send a welcome email upon registration or first Google sign-in."""
        subject = "Welcome to ThinkFree · Independent Thinking Platform"
        html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #07090e; color: #f1f5f9; padding: 40px 20px; }}
    .container {{ max-width: 560px; margin: 0 auto; background: #0c101b; border: 1px solid rgba(255,255,255,0.08); border-radius: 20px; padding: 36px; }}
    h1 {{ font-size: 20px; color: #ffffff; }}
    p {{ font-size: 14px; color: #94a3b8; line-height: 1.6; }}
    .btn {{ display: inline-block; background: #6366f1; color: #ffffff !important; padding: 12px 28px; border-radius: 10px; text-decoration: none; font-weight: 600; font-size: 13px; margin-top: 20px; }}
  </style>
</head>
<body>
  <div class="container">
    <h2 style="color:#6366f1; margin:0 0 16px 0;">ThinkFree</h2>
    <h1>Welcome, {user_name}!</h1>
    <p>Your ThinkFree account has been created. Start solving curriculum challenges, training your Independent Thinking Score (ITS), and locking knowledge into long-term memory with SM-2 spaced repetition.</p>
    <a href="{settings.FRONTEND_URL}" class="btn" target="_blank">Launch Dashboard →</a>
  </div>
</body>
</html>"""
        return await asyncio.to_thread(cls._send_smtp_payload, to_email, subject, html_body)
