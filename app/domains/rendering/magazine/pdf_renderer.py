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
        # 各平台 WeasyPrint 依赖的原生库名/路径不同，在 import 前做平台适配。
        import os, platform
        _sys = platform.system()

        if _sys == "Darwin":
            # macOS Homebrew: cffi 搜索 Linux 风格库名，需 monkey-patch dlopen
            _brew_lib = "/opt/homebrew/lib"
            _lib_map = {
                "gobject-2.0-0": os.path.join(_brew_lib, "libgobject-2.0.0.dylib"),
                "gobject-2.0": os.path.join(_brew_lib, "libgobject-2.0.dylib"),
                "libgobject-2.0-0": os.path.join(_brew_lib, "libgobject-2.0.0.dylib"),
                "pango-1.0-0": os.path.join(_brew_lib, "libpango-1.0.0.dylib"),
                "pango-1.0": os.path.join(_brew_lib, "libpango-1.0.dylib"),
                "libpango-1.0-0": os.path.join(_brew_lib, "libpango-1.0.0.dylib"),
                "pangocairo-1.0-0": os.path.join(_brew_lib, "libpangocairo-1.0.0.dylib"),
                "pangocairo-1.0": os.path.join(_brew_lib, "libpangocairo-1.0.dylib"),
                "pangoft2-1.0-0": os.path.join(_brew_lib, "libpangoft2-1.0.0.dylib"),
                "pangoft2-1.0": os.path.join(_brew_lib, "libpangoft2-1.0.dylib"),
                "libpangoft2-1.0-0": os.path.join(_brew_lib, "libpangoft2-1.0.0.dylib"),
                "fontconfig-1": os.path.join(_brew_lib, "libfontconfig.1.dylib"),
                "fontconfig": os.path.join(_brew_lib, "libfontconfig.dylib"),
                "libfontconfig": os.path.join(_brew_lib, "libfontconfig.dylib"),
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

        elif _sys == "Windows":
            # Windows: GTK3 运行时需要在 PATH 中，常见安装路径：
            #   - MSYS2:  C:\msys64\mingw64\bin
            #   - 独立包: C:\Program Files\GTK3-Runtime Win64\bin
            _gtk_paths = [
                r"C:\msys64\mingw64\bin",
                r"C:\Program Files\GTK3-Runtime Win64\bin",
                os.path.join(os.environ.get("PROGRAMFILES", ""), "GTK3-Runtime Win64", "bin"),
            ]
            for _gp in _gtk_paths:
                if os.path.isdir(_gp) and _gp not in os.environ.get("PATH", ""):
                    os.environ["PATH"] = _gp + os.pathsep + os.environ.get("PATH", "")
                    logger.debug("已将 GTK3 路径加入 PATH: %s", _gp)
                    break

        from weasyprint import HTML, CSS
    except ImportError:
        _install_hints = (
            "weasyprint 未安装或缺少系统依赖，请参考以下步骤:\n"
            "  pip install weasyprint\n"
        )
        _sys_name = platform.system() if "platform" in dir() else "Unknown"
        if _sys_name == "Darwin":
            _install_hints += (
                "macOS 还需要:\n"
                "  brew install cairo pango gdk-pixbuf libffi\n"
            )
        elif _sys_name == "Windows":
            _install_hints += (
                "Windows 还需要安装 GTK3 运行时（提供 cairo/pango 等 DLL）:\n"
                "  方法 A (推荐): 安装 MSYS2 后执行:\n"
                "    pacman -S mingw-w64-x86_64-pango mingw-w64-x86_64-cairo\n"
                "    并将 C:\\msys64\\mingw64\\bin 加入系统 PATH\n"
                "  方法 B: 使用 Docker 环境（推荐生产部署）\n"
            )
        _install_hints += "Docker 环境已通过 Dockerfile 预装依赖（libpango / libcairo / fonts-noto-cjk）"
        raise ImportError(_install_hints)

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
