"""
杂志级 PDF 渲染器（WeasyPrint）

render_pdf(plan_id, session) -> bytes
  调用 html_renderer.render_html() 获取 HTML，再用 WeasyPrint 转为 PDF bytes

WeasyPrint 配置：
  - @page { size: A4; margin: 20mm; }
  - @page :first { margin: 0; }（封面无边距）
  - 字体通过 Dockerfile 预装 fonts-noto-cjk
"""
from __future__ import annotations

import logging
import uuid as _uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.rendering.magazine.html_renderer import render_html

logger = logging.getLogger(__name__)


async def render_pdf(
    plan_id: _uuid.UUID | str,
    session: AsyncSession,
    base_url: Optional[str] = None,
) -> bytes:
    """
    将 ItineraryPlan 渲染为 PDF bytes。

    Args:
        plan_id:  ItineraryPlan UUID
        session:  AsyncSession
        base_url: HTML 中相对 URL 的基础 URL（如 "http://localhost:8000"）
                  WeasyPrint 需要用此解析图片等静态资源

    Returns:
        PDF bytes

    Raises:
        ImportError:  weasyprint 未安装
        ValueError:   plan_id 不存在
    """
    try:
        # macOS Homebrew: WeasyPrint 的 cffi 搜索 Linux 风格的库名，
        # 但 macOS 库名格式不同。在 import 前 monkey-patch cffi 的 dlopen 搜索路径。
        import os, platform
        if platform.system() == "Darwin":
            _brew_lib = "/opt/homebrew/lib"
            _lib_map = {
                # gobject
                "gobject-2.0-0": os.path.join(_brew_lib, "libgobject-2.0.0.dylib"),
                "gobject-2.0": os.path.join(_brew_lib, "libgobject-2.0.dylib"),
                "libgobject-2.0-0": os.path.join(_brew_lib, "libgobject-2.0.0.dylib"),
                # pango
                "pango-1.0-0": os.path.join(_brew_lib, "libpango-1.0.0.dylib"),
                "pango-1.0": os.path.join(_brew_lib, "libpango-1.0.dylib"),
                "libpango-1.0-0": os.path.join(_brew_lib, "libpango-1.0.0.dylib"),
                # pangocairo
                "pangocairo-1.0-0": os.path.join(_brew_lib, "libpangocairo-1.0.0.dylib"),
                "pangocairo-1.0": os.path.join(_brew_lib, "libpangocairo-1.0.dylib"),
                # pangoft2
                "pangoft2-1.0-0": os.path.join(_brew_lib, "libpangoft2-1.0.0.dylib"),
                "pangoft2-1.0": os.path.join(_brew_lib, "libpangoft2-1.0.dylib"),
                "libpangoft2-1.0-0": os.path.join(_brew_lib, "libpangoft2-1.0.0.dylib"),
                # fontconfig
                "fontconfig-1": os.path.join(_brew_lib, "libfontconfig.1.dylib"),
                "fontconfig": os.path.join(_brew_lib, "libfontconfig.dylib"),
                "libfontconfig": os.path.join(_brew_lib, "libfontconfig.dylib"),
                # harfbuzz (WeasyPrint 60 first tries "harfbuzz")
                "harfbuzz": os.path.join(_brew_lib, "libharfbuzz.dylib"),
                "harfbuzz-0": os.path.join(_brew_lib, "libharfbuzz.0.dylib"),
                "harfbuzz-0.0": os.path.join(_brew_lib, "libharfbuzz.0.dylib"),
                "libharfbuzz-0": os.path.join(_brew_lib, "libharfbuzz.0.dylib"),
            }
            if os.path.isdir(_brew_lib):
                try:
                    import cffi
                    _orig_dlopen = cffi.FFI.dlopen
                    def _patched_dlopen(self, name, flags=0):
                        if isinstance(name, str) and name in _lib_map:
                            return _orig_dlopen(self, _lib_map[name], flags)
                        return _orig_dlopen(self, name, flags)
                    cffi.FFI.dlopen = _patched_dlopen
                except Exception:
                    pass
        from weasyprint import HTML, CSS
    except ImportError:
        raise ImportError(
            "weasyprint 未安装，请运行:\n"
            "  pip install weasyprint\n"
            "macOS 还需要:\n"
            "  brew install cairo pango gdk-pixbuf libffi\n"
            "Docker 环境已通过 Dockerfile 预装依赖（libpango / libcairo / fonts-noto-cjk）"
        )

    # 1. 渲染 HTML
    html_content = await render_html(plan_id, session)

    # 2. WeasyPrint 转 PDF
    logger.info("开始 WeasyPrint PDF 渲染 plan=%s", plan_id)
    try:
        html_obj = HTML(
            string=html_content,
            base_url=base_url,  # 用于解析相对路径（图片、CSS）
        )
        pdf_bytes = html_obj.write_pdf()
        logger.info("PDF 渲染完成 plan=%s，大小 %d bytes", plan_id, len(pdf_bytes))
        return pdf_bytes
    except Exception as e:
        logger.error("WeasyPrint 渲染失败 plan=%s: %s", plan_id, e)
        raise
