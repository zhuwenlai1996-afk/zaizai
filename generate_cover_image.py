"""
《7天降脂食谱表》封面图生成器
输出 3 个尺寸:
1. 朋友圈竖版海报(1080×1440)
2. 公众号封面(900×383)
3. 方版社群分享(1080×1080)
"""
import subprocess
from pathlib import Path
from weasyprint import HTML

OUTPUT_DIR = Path("/projects/sandbox/zaizai/cover_images")
OUTPUT_DIR.mkdir(exist_ok=True)


# ============ 共用 CSS 样式 ============
COMMON_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: "Noto Sans CJK SC", sans-serif;
  margin: 0;
  padding: 0;
}

.cover {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: linear-gradient(135deg, #FAF3E7 0%, #F2E5C9 100%);
}

/* 装饰圆形 */
.deco-circle-1 {
  position: absolute;
  width: 280px;
  height: 280px;
  border-radius: 50%;
  background: radial-gradient(circle, #F4A261 0%, transparent 70%);
  opacity: 0.35;
  top: -80px;
  right: -80px;
}

.deco-circle-2 {
  position: absolute;
  width: 220px;
  height: 220px;
  border-radius: 50%;
  background: radial-gradient(circle, #52B788 0%, transparent 70%);
  opacity: 0.3;
  bottom: -60px;
  left: -60px;
}

.deco-leaves {
  position: absolute;
  font-size: 72pt;
  opacity: 0.12;
}

/* 头部小标签 */
.tag {
  display: inline-block;
  background: #2A6F4D;
  color: white;
  padding: 6px 18px;
  font-size: 11pt;
  font-weight: 700;
  letter-spacing: 4px;
  border-radius: 20px;
  margin-bottom: 24px;
}

/* 主标题 */
.main-title {
  font-family: "Noto Serif CJK SC", serif;
  font-weight: 900;
  color: #2A6F4D;
  letter-spacing: 6px;
  line-height: 1.15;
  margin-bottom: 12px;
}

/* 数字"7" */
.number-seven {
  font-family: "Noto Serif CJK SC", serif;
  font-weight: 900;
  color: #F4A261;
  line-height: 0.9;
  display: inline-block;
}

/* 副标题 */
.subtitle {
  color: #666;
  font-weight: 300;
  letter-spacing: 2px;
  margin-bottom: 28px;
}

/* 卖点列表 */
.benefits {
  display: flex;
  justify-content: space-around;
  margin: 28px 0;
}

.benefit {
  text-align: center;
  flex: 1;
}

.benefit-num {
  font-family: "Noto Serif CJK SC", serif;
  font-weight: 900;
  color: #F4A261;
  line-height: 1;
  margin-bottom: 6px;
}

.benefit-text {
  color: #2A6F4D;
  font-weight: 700;
  letter-spacing: 1px;
}

/* 装饰横线 */
.divider {
  width: 60px;
  height: 3px;
  background: #F4A261;
  margin: 18px auto;
  border-radius: 2px;
}

/* 暖色横幅 */
.warm-band {
  background: linear-gradient(90deg, #F4A261 0%, #E76F51 100%);
  color: white;
  padding: 14px 0;
  text-align: center;
  font-weight: 700;
  letter-spacing: 3px;
  border-radius: 6px;
  margin: 24px 0;
  box-shadow: 0 4px 12px rgba(231, 111, 81, 0.3);
}

/* 底部文字 */
.footer-text {
  color: #999;
  font-size: 10pt;
  letter-spacing: 1px;
  text-align: center;
}

.brand {
  color: #2A6F4D;
  font-weight: 700;
}

/* 食物 emoji 装饰 */
.food-icons {
  text-align: center;
  font-size: 32pt;
  letter-spacing: 14px;
  margin: 16px 0;
  filter: saturate(1.1);
}
"""


# ============ 1. 朋友圈竖版海报 1080×1440 (3:4) ============
POSTER_HTML = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
@page {{ size: 270mm 360mm; margin: 0; }}
{COMMON_CSS}

.cover {{
  width: 270mm;
  height: 360mm;
  padding: 60px 50px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}}

.deco-leaves {{ font-size: 96pt; }}
.leaves-1 {{ top: 60px; left: 60px; }}
.leaves-2 {{ bottom: 80px; right: 60px; }}

.poster-tag {{
  display: inline-block;
  background: #2A6F4D;
  color: white;
  padding: 8px 24px;
  font-size: 14pt;
  font-weight: 700;
  letter-spacing: 6px;
  border-radius: 30px;
  margin-bottom: 28px;
}}

.poster-title {{
  font-family: "Noto Serif CJK SC", serif;
  font-weight: 900;
  font-size: 68pt;
  color: #2A6F4D;
  letter-spacing: 8px;
  line-height: 1.15;
  margin-bottom: 18px;
}}

.poster-title .seven {{
  color: #F4A261;
  font-size: 88pt;
  display: inline-block;
  vertical-align: middle;
  margin-right: 6px;
}}

.poster-subtitle {{
  font-size: 18pt;
  color: #666;
  font-weight: 300;
  letter-spacing: 4px;
  margin-bottom: 36px;
}}

.poster-question {{
  background: #FFFFFF;
  border-left: 6px solid #E76F51;
  padding: 18px 24px;
  border-radius: 4px;
  font-size: 17pt;
  color: #444;
  line-height: 1.6;
  margin: 24px 0 32px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}}

.poster-question b {{
  color: #E76F51;
  font-size: 19pt;
}}

.poster-benefits {{
  display: flex;
  justify-content: space-between;
  margin: 28px 0;
  gap: 16px;
}}

.poster-benefit {{
  flex: 1;
  background: white;
  border-radius: 12px;
  padding: 24px 12px;
  text-align: center;
  box-shadow: 0 4px 16px rgba(42, 111, 77, 0.1);
  border-top: 4px solid #F4A261;
}}

.poster-benefit-num {{
  font-family: "Noto Serif CJK SC", serif;
  font-weight: 900;
  font-size: 42pt;
  color: #F4A261;
  line-height: 1;
  margin-bottom: 8px;
}}

.poster-benefit-text {{
  font-size: 14pt;
  color: #2A6F4D;
  font-weight: 700;
  letter-spacing: 2px;
}}

.poster-band {{
  background: linear-gradient(90deg, #F4A261 0%, #E76F51 100%);
  color: white;
  padding: 22px 0;
  text-align: center;
  font-size: 18pt;
  font-weight: 700;
  letter-spacing: 5px;
  border-radius: 8px;
  margin: 36px 0 24px;
  box-shadow: 0 6px 20px rgba(231, 111, 81, 0.35);
}}

.poster-foods {{
  text-align: center;
  font-size: 36pt;
  letter-spacing: 18px;
  margin: 18px 0;
}}

.poster-footer {{
  text-align: center;
  font-size: 13pt;
  color: #999;
  letter-spacing: 2px;
  padding-top: 16px;
  border-top: 1px dashed #ccc;
}}

.poster-footer .brand {{
  color: #2A6F4D;
  font-weight: 700;
  font-size: 15pt;
  display: block;
  margin-bottom: 6px;
}}
</style></head>
<body>
<div class="cover">
  <div class="deco-circle-1"></div>
  <div class="deco-circle-2"></div>
  <div class="deco-leaves leaves-1">🌿</div>
  <div class="deco-leaves leaves-2">🍃</div>

  <div>
    <div class="poster-tag">公 众 号 粉 丝 福 利</div>
    <h1 class="poster-title">
      <span class="seven">7</span>天<br>
      降脂食谱表
    </h1>
    <div class="poster-subtitle">—— 给查出血管斑块的你和家人 ——</div>

    <div class="poster-question">
      体检报告上的<b>"斑块"</b>两个字,<br>
      不是判决书,是一封提醒信。
    </div>

    <div class="poster-benefits">
      <div class="poster-benefit">
        <div class="poster-benefit-num">0</div>
        <div class="poster-benefit-text">花费</div>
      </div>
      <div class="poster-benefit">
        <div class="poster-benefit-num">21</div>
        <div class="poster-benefit-text">天见效</div>
      </div>
      <div class="poster-benefit">
        <div class="poster-benefit-num">7.3<span style="font-size:24pt">%</span></div>
        <div class="poster-benefit-text">斑块缩小</div>
      </div>
    </div>
  </div>

  <div>
    <div class="poster-foods">🥣 🐟 🥦 🫐 🥜</div>
    <div class="poster-band">在家做 · 中国家庭口味</div>
    <div class="poster-footer">
      <span class="brand">健康公众号</span>
      关注 + 留言「我开始养血管」即可领取
    </div>
  </div>
</div>
</body></html>
"""


# ============ 2. 公众号头条封面 900×383 (2.35:1) ============
WECHAT_HTML = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
@page {{ size: 225mm 95.7mm; margin: 0; }}
{COMMON_CSS}

.cover {{
  width: 225mm;
  height: 95.7mm;
  padding: 24px 40px;
  display: flex;
  align-items: center;
  gap: 32px;
}}

.wechat-left {{
  flex: 0 0 auto;
  text-align: center;
}}

.wechat-seven {{
  font-family: "Noto Serif CJK SC", serif;
  font-weight: 900;
  font-size: 96pt;
  color: #F4A261;
  line-height: 1;
  margin-bottom: -4px;
}}

.wechat-day {{
  font-size: 13pt;
  color: #2A6F4D;
  font-weight: 700;
  letter-spacing: 6px;
}}

.wechat-divider {{
  width: 2px;
  height: 60mm;
  background: #2A6F4D;
  opacity: 0.3;
}}

.wechat-right {{
  flex: 1;
}}

.wechat-tag {{
  display: inline-block;
  background: #2A6F4D;
  color: white;
  padding: 4px 14px;
  font-size: 9pt;
  font-weight: 700;
  letter-spacing: 3px;
  border-radius: 12px;
  margin-bottom: 12px;
}}

.wechat-title {{
  font-family: "Noto Serif CJK SC", serif;
  font-weight: 900;
  font-size: 32pt;
  color: #2A6F4D;
  letter-spacing: 4px;
  line-height: 1.1;
  margin-bottom: 8px;
}}

.wechat-subtitle {{
  font-size: 12pt;
  color: #666;
  font-weight: 300;
  letter-spacing: 2px;
  margin-bottom: 14px;
}}

.wechat-points {{
  display: flex;
  gap: 12px;
}}

.wechat-point {{
  background: white;
  padding: 6px 14px;
  border-radius: 16px;
  font-size: 10pt;
  color: #2A6F4D;
  font-weight: 700;
  letter-spacing: 1px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.08);
  border: 1px solid #F4A261;
}}
</style></head>
<body>
<div class="cover">
  <div class="deco-circle-1" style="width:180px;height:180px;top:-50px;right:-30px;"></div>
  <div class="deco-circle-2" style="width:140px;height:140px;bottom:-40px;left:-20px;"></div>

  <div class="wechat-left">
    <div class="wechat-seven">7</div>
    <div class="wechat-day">天 降 脂 食 谱</div>
  </div>

  <div class="wechat-divider"></div>

  <div class="wechat-right">
    <div class="wechat-tag">体 检 查 出 斑 块 必 看</div>
    <h1 class="wechat-title">把血管慢慢养回来</h1>
    <div class="wechat-subtitle">0花费 · 在家做 · 中国家庭口味</div>
    <div class="wechat-points">
      <span class="wechat-point">🥣 燕麦+深海鱼</span>
      <span class="wechat-point">🥦 红绿灯食物</span>
      <span class="wechat-point">📏 手掌量勺</span>
    </div>
  </div>
</div>
</body></html>
"""


# ============ 3. 方版社群分享 1080×1080 (1:1) ============
SQUARE_HTML = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
@page {{ size: 270mm 270mm; margin: 0; }}
{COMMON_CSS}

.cover {{
  width: 270mm;
  height: 270mm;
  padding: 50px 50px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}}

.sq-tag {{
  display: inline-block;
  background: #2A6F4D;
  color: white;
  padding: 7px 20px;
  font-size: 12pt;
  font-weight: 700;
  letter-spacing: 4px;
  border-radius: 24px;
  margin-bottom: 24px;
}}

.sq-title {{
  font-family: "Noto Serif CJK SC", serif;
  font-weight: 900;
  font-size: 60pt;
  color: #2A6F4D;
  letter-spacing: 8px;
  line-height: 1.1;
  margin-bottom: 14px;
}}

.sq-title .seven {{
  color: #F4A261;
  font-size: 78pt;
  display: inline-block;
  vertical-align: middle;
  margin-right: 4px;
}}

.sq-subtitle {{
  font-size: 16pt;
  color: #666;
  font-weight: 300;
  letter-spacing: 3px;
  margin-bottom: 28px;
}}

.sq-quote {{
  background: #FFFFFF;
  border-left: 5px solid #E76F51;
  padding: 16px 22px;
  border-radius: 4px;
  font-size: 15pt;
  color: #444;
  line-height: 1.6;
  margin-bottom: 28px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}}

.sq-quote b {{
  color: #E76F51;
  font-size: 17pt;
}}

.sq-benefits {{
  display: flex;
  justify-content: space-between;
  gap: 14px;
}}

.sq-benefit {{
  flex: 1;
  background: white;
  border-radius: 10px;
  padding: 20px 8px;
  text-align: center;
  box-shadow: 0 3px 12px rgba(42, 111, 77, 0.1);
  border-top: 3px solid #F4A261;
}}

.sq-benefit-num {{
  font-family: "Noto Serif CJK SC", serif;
  font-weight: 900;
  font-size: 36pt;
  color: #F4A261;
  line-height: 1;
  margin-bottom: 6px;
}}

.sq-benefit-text {{
  font-size: 12pt;
  color: #2A6F4D;
  font-weight: 700;
  letter-spacing: 2px;
}}

.sq-band {{
  background: linear-gradient(90deg, #F4A261 0%, #E76F51 100%);
  color: white;
  padding: 18px 0;
  text-align: center;
  font-size: 15pt;
  font-weight: 700;
  letter-spacing: 4px;
  border-radius: 6px;
  margin: 26px 0 18px;
  box-shadow: 0 4px 14px rgba(231, 111, 81, 0.3);
}}

.sq-foods {{
  text-align: center;
  font-size: 30pt;
  letter-spacing: 16px;
  margin: 12px 0;
}}

.sq-footer {{
  text-align: center;
  font-size: 11pt;
  color: #999;
  letter-spacing: 1px;
}}

.sq-footer .brand {{
  color: #2A6F4D;
  font-weight: 700;
  font-size: 12pt;
}}
</style></head>
<body>
<div class="cover">
  <div class="deco-circle-1"></div>
  <div class="deco-circle-2"></div>
  <div class="deco-leaves" style="top:50px;left:50px;font-size:80pt;">🌿</div>
  <div class="deco-leaves" style="bottom:60px;right:50px;font-size:80pt;">🍃</div>

  <div>
    <div class="sq-tag">公 众 号 粉 丝 福 利</div>
    <h1 class="sq-title">
      <span class="seven">7</span>天<br>
      降脂食谱表
    </h1>
    <div class="sq-subtitle">—— 给查出血管斑块的你和家人 ——</div>

    <div class="sq-quote">
      体检报告上的 <b>"斑块"</b> 两个字,<br>
      不是判决书,是一封提醒信。
    </div>

    <div class="sq-benefits">
      <div class="sq-benefit">
        <div class="sq-benefit-num">0</div>
        <div class="sq-benefit-text">花费</div>
      </div>
      <div class="sq-benefit">
        <div class="sq-benefit-num">21</div>
        <div class="sq-benefit-text">天见效</div>
      </div>
      <div class="sq-benefit">
        <div class="sq-benefit-num">7.3<span style="font-size:18pt">%</span></div>
        <div class="sq-benefit-text">斑块缩小</div>
      </div>
    </div>
  </div>

  <div>
    <div class="sq-foods">🥣 🐟 🥦 🫐 🥜</div>
    <div class="sq-band">在家做 · 中国家庭口味</div>
    <div class="sq-footer">
      <span class="brand">健康公众号</span> · 关注 + 留言「我开始养血管」即可领取
    </div>
  </div>
</div>
</body></html>
"""


def render(html_str, name, target_width):
    """HTML → PDF → PNG (使用 pymupdf 渲染,无需 poppler)"""
    import fitz  # pymupdf
    from PIL import Image
    import io

    pdf_path = OUTPUT_DIR / f"{name}.pdf"
    png_path = OUTPUT_DIR / f"{name}.png"

    # 渲染为 PDF
    HTML(string=html_str).write_pdf(str(pdf_path))

    # PDF → PNG (高 DPI)
    doc = fitz.open(str(pdf_path))
    page = doc[0]
    # 用高分辨率渲染 (3x ≈ 216 DPI)
    mat = fitz.Matrix(3.0, 3.0)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img_data = pix.tobytes("png")
    doc.close()

    img = Image.open(io.BytesIO(img_data))

    # 调整到目标宽度
    if img.width != target_width:
        ratio = target_width / img.width
        new_size = (target_width, int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    img.save(png_path, "PNG", optimize=True)

    # 移除中间 PDF
    pdf_path.unlink()

    size_kb = png_path.stat().st_size / 1024
    print(f"✅ {name}.png  ({img.width}×{img.height}, {size_kb:.0f} KB)")


def main():
    print("正在生成封面图...\n")

    render(POSTER_HTML, "01_朋友圈竖版海报_1080x1440", 1080)
    render(WECHAT_HTML, "02_公众号头条封面_900x383", 900)
    render(SQUARE_HTML, "03_方版社群分享_1080x1080", 1080)

    print(f"\n📁 全部输出至:{OUTPUT_DIR}")


if __name__ == "__main__":
    main()
