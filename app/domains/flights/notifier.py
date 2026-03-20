"""
app/domains/flights/notifier.py

特价提醒通知：
- 企业微信机器人 Webhook（主要渠道）
- 邮件（SMTP 备用）
"""
from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# 城市名称映射
AIRPORT_NAME: dict[str, str] = {
    "SHA": "上海", "PEK": "北京", "CAN": "广州",
    "CTU": "成都", "SZX": "深圳",
    "TYO": "东京", "OSA": "大阪", "NGO": "名古屋",
}


def _build_message(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str],
    price: float,
    currency: str,
    is_new_low: bool,
    historical_low: Optional[float],
) -> str:
    origin_name = AIRPORT_NAME.get(origin, origin)
    dest_name = AIRPORT_NAME.get(destination, destination)
    tag = "🆕 历史新低！" if is_new_low else "💥 特价来了！"
    hist_str = f"¥{historical_low:.0f}" if historical_low else "首次记录"
    ret_str = f" → {return_date}" if return_date else ""

    lines = [
        f"{tag}",
        f"✈️ {origin_name} → {dest_name}",
        f"📅 {departure_date}{ret_str}",
        f"💰 最低 **¥{price:.0f}** {currency}",
        f"📊 历史低价: {hist_str}",
        f"🔗 立即查票: https://flights.ctrip.com",
    ]
    return "\n".join(lines)


async def send_wecom_alert(message: str) -> bool:
    """发送企业微信机器人通知"""
    webhook = getattr(settings, "wecom_webhook_url", None)
    if not webhook:
        logger.debug("未配置 WECOM_WEBHOOK_URL，跳过企业微信通知")
        return False

    payload = {
        "msgtype": "markdown",
        "markdown": {"content": message},
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(webhook, json=payload)
            resp.raise_for_status()
            data = resp.json()
            if data.get("errcode") == 0:
                logger.info("企业微信通知发送成功")
                return True
            else:
                logger.warning("企业微信通知失败: %s", data)
                return False
    except Exception as e:
        logger.warning("企业微信通知异常: %s", e)
        return False


def send_email_alert(message: str, subject: str = "日本机票特价提醒") -> bool:
    """发送邮件通知（同步，用于 fallback）"""
    smtp_host = getattr(settings, "smtp_host", None)
    smtp_user = getattr(settings, "smtp_user", None)
    smtp_pass = getattr(settings, "smtp_password", None)
    alert_email = getattr(settings, "alert_email", None)

    if not all([smtp_host, smtp_user, smtp_pass, alert_email]):
        logger.debug("未配置 SMTP，跳过邮件通知")
        return False

    try:
        msg = MIMEText(message, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = alert_email

        with smtplib.SMTP_SSL(smtp_host, 465) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [alert_email], msg.as_string())
        logger.info("邮件通知发送成功 → %s", alert_email)
        return True
    except Exception as e:
        logger.warning("邮件通知失败: %s", e)
        return False


async def send_price_alert(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str],
    price: float,
    currency: str,
    is_new_low: bool = False,
    historical_low: Optional[float] = None,
) -> None:
    """统一通知入口：企业微信优先，失败则邮件"""
    message = _build_message(
        origin, destination, departure_date, return_date,
        price, currency, is_new_low, historical_low,
    )

    sent = await send_wecom_alert(message)
    if not sent:
        send_email_alert(message)
