"""
convert_md_to_pdf.py — 把指定目录下的 .md 文件批量转为 PDF（fpdf2 + 中文字体）

用法:
  python scripts/convert_md_to_pdf.py [--input-dir DIR] [--output-dir DIR]
"""
import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _find_font():
    """查找可用中文字体"""
    candidates = [
        Path(__file__).parent / "_fonts" / "NotoSansSC-Regular.ttf",
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\simsun.ttc",
    ]
    for f in candidates:
        p = Path(f)
        if p.exists():
            return str(p)
    return None


def md_to_pdf(md_path: Path, pdf_path: Path, font_path: str | None):
    """将单个 MD 文件转为 PDF"""
    from fpdf import FPDF

    text = md_path.read_text(encoding="utf-8")

    class MdPDF(FPDF):
        def __init__(self):
            super().__init__()
            self._zh = "Helvetica"
            if font_path and (font_path.endswith(".ttf") or font_path.endswith(".ttc")):
                self.add_font("zh", "", font_path, uni=True)
                self.add_font("zh", "B", font_path, uni=True)
                self._zh = "zh"

        def header(self):
            if self.page_no() == 1:
                return
            self.set_font(self._zh, "", 7)
            self.set_text_color(170, 170, 170)
            self.cell(0, 5, md_path.stem, align="R", new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(220, 220, 220)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(2)

        def footer(self):
            self.set_y(-12)
            self.set_font(self._zh, "", 7)
            self.set_text_color(170, 170, 170)
            self.cell(0, 8, f"— {self.page_no()} —", align="C")

    pdf = MdPDF()
    zh = pdf._zh
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # 封面：文件名作为标题
    pdf.ln(30)
    pdf.set_font(zh, "B", 22)
    pdf.set_text_color(35, 35, 35)
    title = md_path.stem.replace("-", " ").replace("_", " ").title()
    pdf.multi_cell(0, 12, title, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)
    pdf.set_font(zh, "", 10)
    pdf.set_text_color(130, 130, 130)
    pdf.cell(0, 7, f"源文件: {md_path.name}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, "Travel AI · 审计文档", align="C", new_x="LMARGIN", new_y="NEXT")

    # 正文
    pdf.add_page()

    lines = text.split("\n")
    for line in lines:
        stripped = line.strip()

        # Heading
        if stripped.startswith("### "):
            pdf.ln(3)
            pdf.set_font(zh, "B", 11)
            pdf.set_text_color(60, 90, 140)
            pdf.multi_cell(0, 7, stripped[4:], new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
        elif stripped.startswith("## "):
            pdf.ln(4)
            pdf.set_font(zh, "B", 13)
            pdf.set_text_color(40, 70, 120)
            pdf.multi_cell(0, 8, stripped[3:], new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
        elif stripped.startswith("# "):
            pdf.ln(5)
            pdf.set_font(zh, "B", 16)
            pdf.set_text_color(35, 35, 35)
            pdf.multi_cell(0, 10, stripped[2:], new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)
        elif stripped.startswith("---") or stripped.startswith("==="):
            pdf.set_draw_color(200, 200, 200)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(3)
        elif stripped.startswith("- ") or stripped.startswith("* "):
            pdf.set_font(zh, "", 9)
            pdf.set_text_color(60, 60, 60)
            pdf.set_x(15)
            pdf.multi_cell(175, 5, f"·  {stripped[2:]}", new_x="LMARGIN", new_y="NEXT")
        elif re.match(r"^\d+\.", stripped):
            pdf.set_font(zh, "", 9)
            pdf.set_text_color(60, 60, 60)
            pdf.set_x(15)
            pdf.multi_cell(175, 5, stripped, new_x="LMARGIN", new_y="NEXT")
        elif stripped.startswith("```"):
            pdf.set_font(zh, "", 8)
            pdf.set_text_color(80, 80, 80)
            pdf.set_fill_color(245, 245, 245)
            # 代码块开始/结束标记，跳过
        elif stripped.startswith(">"):
            pdf.set_font(zh, "", 9)
            pdf.set_text_color(100, 100, 100)
            pdf.set_fill_color(248, 248, 248)
            pdf.set_x(15)
            pdf.multi_cell(175, 5, stripped.lstrip("> "), fill=True, new_x="LMARGIN", new_y="NEXT")
        elif stripped == "":
            pdf.ln(2)
        else:
            # 普通文本
            pdf.set_font(zh, "", 9)
            pdf.set_text_color(50, 50, 50)
            pdf.multi_cell(0, 5, stripped, new_x="LMARGIN", new_y="NEXT")

    pdf.output(str(pdf_path))
    print(f"  ✅ {pdf_path.name} ({pdf.pages_count} 页)")


def main():
    parser = argparse.ArgumentParser(description="MD → PDF 批量转换")
    parser.add_argument(
        "--input-dir",
        default="openspec/changes/generation-link-convergence",
        help="MD 文件所在目录",
    )
    parser.add_argument(
        "--output-dir",
        default="output/audit-pdfs",
        help="PDF 输出目录",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    font = _find_font()
    if font:
        print(f"🔤 使用字体: {font}")
    else:
        print("⚠️ 未找到中文字体，PDF 中文可能乱码")

    md_files = sorted(input_dir.glob("*.md"))
    if not md_files:
        print(f"❌ {input_dir} 下没有 .md 文件")
        return

    print(f"\n📄 共 {len(md_files)} 个 MD 文件 → PDF\n")
    for md_file in md_files:
        pdf_name = md_file.stem + ".pdf"
        pdf_path = output_dir / pdf_name
        try:
            md_to_pdf(md_file, pdf_path, font)
        except Exception as e:
            print(f"  ❌ {md_file.name}: {e}")

    print(f"\n📁 所有 PDF 输出到: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
