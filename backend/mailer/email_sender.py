from config import get_settings
from utils.logger import logger

settings = get_settings()


def send_password_reset_email(to_email: str, full_name: str, reset_link: str) -> None:
    """Send a password reset email using the configured provider."""
    if settings.EMAIL_PROVIDER == "resend":
        _send_via_resend(to_email, full_name, reset_link)
    elif settings.EMAIL_PROVIDER == "smtp":
        _send_via_smtp(to_email, full_name, reset_link)
    else:
        # Local fallback: just log the link
        logger.info(f"[EMAIL] Reset link for {to_email}: {reset_link}")


def _send_via_resend(to_email: str, full_name: str, reset_link: str) -> None:
    """Send email using Resend API."""
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set, logging reset link instead")
        logger.info(f"[EMAIL] Reset link for {to_email}: {reset_link}")
        return

    import resend
    resend.api_key = settings.RESEND_API_KEY

    resend.Emails.send({
        "from": settings.EMAIL_FROM_ADDRESS,
        "to": [to_email],
        "subject": "DocMind AI — Password Reset",
        "html": _build_html(full_name, reset_link),
    })
    logger.info(f"Reset email sent to {to_email} via Resend")


def _send_via_smtp(to_email: str, full_name: str, reset_link: str) -> None:
    """Send email using SMTP."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "DocMind AI — Password Reset"
    msg["From"] = settings.EMAIL_FROM_ADDRESS
    msg["To"] = to_email
    msg.attach(MIMEText(_build_html(full_name, reset_link), "html"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.EMAIL_FROM_ADDRESS, to_email, msg.as_string())

    logger.info(f"Reset email sent to {to_email} via SMTP")


def _build_html(full_name: str, reset_link: str) -> str:
    return f"""
    <div style="font-family: 'DM Sans', sans-serif; max-width: 480px; margin: 0 auto; padding: 32px;">
        <h2 style="color: #5B6CF6;">DocMind AI</h2>
        <p>Hi {full_name},</p>
        <p>You requested a password reset. Click the button below to set a new password:</p>
        <p style="text-align: center; margin: 24px 0;">
            <a href="{reset_link}"
               style="background: #5B6CF6; color: white; padding: 12px 24px;
                      border-radius: 8px; text-decoration: none; font-weight: 600;">
                Reset Password
            </a>
        </p>
        <p style="color: #888; font-size: 14px;">
            This link expires in 30 minutes. If you didn't request this, ignore this email.
        </p>
    </div>
    """
