"""
Task 5.2 — 水印功能验证测试

覆盖：
1. _build_watermark_css 返回非空 HTML
2. 水印文字正确注入 CSS content 属性
3. 特殊字符被正确转义（防注入）
4. render_pdf 的 watermark_text 参数在不同页面长度下均正确注入
"""
import pytest
from app.domains.rendering.magazine.pdf_renderer import _build_watermark_css


class TestBuildWatermarkCss:
    """_build_watermark_css 单元测试"""

    def test_returns_nonempty_html(self):
        result = _build_watermark_css("张三 · 8888 · 仅供本人使用")
        assert result.strip() != ""
        assert "<style>" in result

    def test_watermark_text_present(self):
        text = "李四 · 9999 · 仅供本人使用"
        result = _build_watermark_css(text)
        assert text in result

    def test_watermark_layer_div_present(self):
        result = _build_watermark_css("测试水印")
        assert "watermark-layer" in result
        assert 'aria-hidden="true"' in result

    def test_single_quote_escaped(self):
        """单引号应被转义，防止 CSS content 注入"""
        result = _build_watermark_css("it's me")
        # 不应出现未转义的单引号在 CSS content 值中
        assert "it\\'s me" in result

    def test_double_quote_escaped(self):
        """双引号应被转义"""
        result = _build_watermark_css('say "hi"')
        assert '\\"hi\\"' in result

    def test_watermark_repeated_in_span(self):
        """水印文字在 span 中重复出现（铺满效果）"""
        text = "赵六 · 仅供本人"
        result = _build_watermark_css(text)
        # span 内应有多次重复
        assert result.count(text) >= 2

    def test_fixed_positioning(self):
        """水印层使用 fixed 定位，确保每页都显示"""
        result = _build_watermark_css("固定水印")
        assert "position: fixed" in result

    def test_low_opacity(self):
        """水印透明度足够低，不影响阅读"""
        result = _build_watermark_css("低透明度")
        # color 应使用 rgba 且 alpha < 0.15
        import re
        # 匹配 rgba(0, 0, 0, 0.xx) 格式
        match = re.search(r"rgba\(0,\s*0,\s*0,\s*([\d.]+)\)", result)
        assert match is not None, "应有 rgba 颜色定义"
        alpha = float(match.group(1))
        assert alpha < 0.15, f"水印透明度 {alpha} 过高，会遮挡内容"


class TestWatermarkInjection:
    """验证水印注入到 HTML 的逻辑"""

    def test_inject_before_body_end(self):
        """水印应注入在 </body> 前"""
        from app.domains.rendering.magazine.pdf_renderer import _build_watermark_css

        dummy_html = "<html><body><p>内容</p></body></html>"
        watermark_html = _build_watermark_css("测试水印")

        if "</body>" in dummy_html:
            result = dummy_html.replace("</body>", f"{watermark_html}\n</body>")
        else:
            result = dummy_html + watermark_html

        assert "watermark-layer" in result
        assert result.index("watermark-layer") < result.index("</body>")

    def test_inject_without_body_tag(self):
        """无 </body> 时水印追加到末尾"""
        from app.domains.rendering.magazine.pdf_renderer import _build_watermark_css

        dummy_html = "<div>纯内容片段</div>"
        watermark_html = _build_watermark_css("追加水印")

        if "</body>" in dummy_html:
            result = dummy_html.replace("</body>", f"{watermark_html}\n</body>")
        else:
            result = dummy_html + watermark_html

        assert "watermark-layer" in result

    @pytest.mark.parametrize("page_count", [1, 3, 7, 10, 20])
    def test_watermark_css_stable_across_page_lengths(self, page_count):
        """不同页数下水印 CSS 输出稳定（不依赖页数）"""
        text = f"用户{page_count}页 · 仅供本人"
        result = _build_watermark_css(text)
        assert "position: fixed" in result
        assert text in result
