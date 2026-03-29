"""Admin HTTP Basic 认证依赖。"""
from __future__ import annotations

import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.core.config import settings

_http_basic = HTTPBasic()


def verify_admin_token(credentials: HTTPBasicCredentials = Depends(_http_basic)) -> None:
    """验证 Admin 端点的 HTTP Basic 认证（username=admin, password=ADMIN_PASSWORD env）。"""
    correct_password = settings.admin_password.encode("utf-8")
    provided_password = credentials.password.encode("utf-8")
    password_ok = secrets.compare_digest(provided_password, correct_password)
    username_ok = secrets.compare_digest(credentials.username.encode("utf-8"), b"admin")
    if not (password_ok and username_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )
