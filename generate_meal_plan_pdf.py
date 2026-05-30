"""
《7天降脂食谱表》PDF 生成器(weasyprint 版本)
For WeChat 公众号 粉丝福利
"""
from weasyprint import HTML, CSS
from pathlib import Path

OUTPUT_PDF = "/projects/sandbox/zaizai/7天降脂食谱表.pdf"

# ============ 7 天食谱数据 ============
MEALS = [
    {
        "day": "Day 1", "weekday": "周一",
        "theme": "燕麦 + 深海鱼,温和开局",
        "breakfast": "燕麦粥 40g · 无糖豆浆 250ml · 水煮蛋 1 个 · 蓝莓 10 颗",
        "lunch": "糙米饭一拳 · 清蒸鲈鱼一掌心 · 凉拌菠菜 · 焯西兰花",
        "dinner": "杂粮粥 1 碗 · 清炒油麦菜 · 老豆腐 100g",
        "snack": "原味核桃 3 颗 · 苹果半个",
        "tip": "燕麦 β-葡聚糖能结合胆汁酸排出,逼肝脏消耗坏胆固醇",
    },
    {
        "day": "Day 2", "weekday": "周二",
        "theme": "豆制品日,植物蛋白当主角",
        "breakfast": "全麦面包 2 片 · 鹰嘴豆泥 1 勺 · 番茄 2 片 · 黑咖啡",
        "lunch": "藜麦饭半碗 · 麻婆豆腐(少油版) · 蒜蓉空心菜 · 紫菜蛋花汤",
        "dinner": "南瓜小米粥 · 蒸毛豆 · 凉拌黄瓜木耳",
        "snack": "无糖酸奶 100g · 巴旦木 10 颗",
        "tip": "大豆异黄酮可调节血脂,每天大豆制品 25g 最佳",
    },
    {
        "day": "Day 3", "weekday": "周三",
        "theme": "深海鱼复盘,Omega-3 补给",
        "breakfast": "燕麦粥配奇亚籽 1 勺 · 水煮蛋 1 个 · 圣女果 5 颗",
        "lunch": "糙米饭一拳 · 香煎三文鱼一掌心 · 蒜蓉芦笋 · 海带豆腐汤",
        "dinner": "玉米 1 根 · 清蒸虾 6 只 · 白灼西兰花",
        "snack": "无糖燕麦奶 200ml · 蓝莓一小把",
        "tip": "三文鱼 / 沙丁鱼 / 鲭鱼,每周吃 2-3 次,抗炎效果最佳",
    },
    {
        "day": "Day 4", "weekday": "周四",
        "theme": "高纤膳食,清肠减负",
        "breakfast": "杂粮馒头 1 个 · 无糖豆浆 250ml · 拌秋葵 · 鸡蛋 1 个",
        "lunch": "荞麦面 1 碗 · 鸡胸肉 100g · 凉拌紫甘蓝胡萝卜丝",
        "dinner": "红薯 1 个(中) · 香菇青菜 · 番茄豆腐汤",
        "snack": "石榴半个 · 南瓜籽一小把",
        "tip": "膳食纤维每日 25-30g,相当于 500g 蔬菜 + 1 拳粗粮",
    },
    {
        "day": "Day 5", "weekday": "周五",
        "theme": "白肉日,温和补蛋白",
        "breakfast": "燕麦糊 1 碗 · 茶叶蛋 1 个 · 火龙果半个",
        "lunch": "糙米饭一拳 · 香菇蒸鸡胸 · 蒜蓉菠菜 · 冬瓜虾皮汤",
        "dinner": "杂粮粥 · 蒜蓉茼蒿 · 凉拌豆腐皮",
        "snack": "希腊酸奶 100g · 草莓 5 颗",
        "tip": "去皮鸡胸 / 虾仁是优质低脂蛋白,优先于红肉",
    },
    {
        "day": "Day 6", "weekday": "周六",
        "theme": "轻断食日,给血管放假",
        "breakfast": "燕麦粥配亚麻籽 · 水煮蛋 1 个 · 猕猴桃 1 个",
        "lunch": "蔬菜沙拉 + 水煮鸡胸 80g · 橄榄油醋汁",
        "dinner": "南瓜浓汤 1 碗 · 蒸杂蔬(西兰花 / 胡萝卜 / 玉米)",
        "snack": "原味坚果 15g(两餐之间)",
        "tip": "周末轻断食(总热量 1200kcal 左右),给代谢系统减压",
    },
    {
        "day": "Day 7", "weekday": "周日",
        "theme": "犒赏日,健康也能有滋味",
        "breakfast": "全麦三明治(蛋 + 牛油果 + 番茄) · 无糖拿铁 1 杯",
        "lunch": "藜麦饭一拳 · 番茄炖牛腩(瘦肉 80g) · 蒜蓉菜心 · 紫菜汤",
        "dinner": "韭菜鸡蛋饺子 8 个(全麦皮) · 凉拌木耳",
        "snack": "黑巧克力(可可 ≥70%)2 小块 · 杏仁 5 颗",
        "tip": "每周允许 1 次小犒赏,可持续才是好方案",
    },
]


def render_meals_html(meals):
    cards = []
    for m in meals:
        cards.append(f"""
        <div class="day-card">
          <div class="day-header">
            <div class="day-tag">
              <span class="day-num">{m['day']}</span>
              <span class="day-week">· {m['weekday']}</span>
            </div>
            <div class="day-theme">{m['theme']}</div>
          </div>
          <table class="meal-table">
            <tr><td class="meal-label">早餐</td><td class="meal-content">{m['breakfast']}</td></tr>
            <tr><td class="meal-label">午餐</td><td class="meal-content">{m['lunch']}</td></tr>
            <tr><td class="meal-label">晚餐</td><td class="meal-content">{m['dinner']}</td></tr>
            <tr><td class="meal-label">加餐</td><td class="meal-content">{m['snack']}</td></tr>
          </table>
          <div class="day-tip">
            <span class="tip-icon">💡</span>
            <span class="tip-text"><b>今日小贴士:</b>{m['tip']}</span>
          </div>
        </div>
        """)
    return "\n".join(cards)


HTML_TEMPLATE = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>7天降脂食谱表</title>
<style>
  @page {{
    size: A4;
    margin: 1.8cm 1.8cm 2cm 1.8cm;
    @bottom-center {{
      content: "《7天降脂食谱表》 · 第 " counter(page) " 页 / 共 " counter(pages) " 页";
      font-family: "Noto Sans CJK SC", sans-serif;
      font-size: 9pt;
      color: #999;
    }}
  }}

  * {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }}

  body {{
    font-family: "Noto Sans CJK SC", "PingFang SC", sans-serif;
    font-size: 10.5pt;
    line-height: 1.7;
    color: #2C3E2D;
    -weasy-font-feature-settings: "kern", "palt";
  }}

  /* ===== 封面 ===== */
  .cover {{
    text-align: center;
    padding-top: 0.5cm;
    page-break-after: always;
  }}

  .cover-title {{
    font-family: "Noto Serif CJK SC", serif;
    font-size: 32pt;
    font-weight: 900;
    color: #2A6F4D;
    letter-spacing: 4px;
    margin-bottom: 8px;
  }}

  .cover-subtitle {{
    font-size: 11pt;
    color: #888;
    margin-bottom: 18px;
    font-weight: 300;
  }}

  .cover-band {{
    background: linear-gradient(90deg, #F4A261, #E76F51);
    color: white;
    padding: 12px 0;
    font-size: 11.5pt;
    font-weight: 700;
    letter-spacing: 2px;
    margin: 16px 0 28px;
    border-radius: 4px;
  }}

  /* ===== 通用模块 ===== */
  .section-h1 {{
    font-size: 16pt;
    color: #2A6F4D;
    font-weight: 700;
    margin: 22px 0 12px;
    padding-left: 12px;
    border-left: 5px solid #F4A261;
  }}

  .section-h2 {{
    font-size: 12.5pt;
    color: #F4A261;
    font-weight: 700;
    margin: 16px 0 8px;
  }}

  /* 介绍卡片 */
  .intro-box {{
    background: #FAF3E7;
    border: 1px solid #2A6F4D;
    border-radius: 6px;
    padding: 16px 20px;
    text-align: left;
    margin-bottom: 20px;
    font-size: 10.5pt;
    line-height: 1.85;
  }}

  .intro-box b {{
    color: #2A6F4D;
  }}

  /* 红绿灯食物清单 */
  .food-table {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 20px;
    border-radius: 6px;
    overflow: hidden;
    border: 1px solid #2A6F4D;
  }}

  .food-table th {{
    color: white;
    padding: 10px 8px;
    font-size: 11pt;
    font-weight: 700;
    text-align: center;
  }}

  .food-table th.green {{ background: #52B788; }}
  .food-table th.yellow {{ background: #F4A261; }}
  .food-table th.red {{ background: #E76F51; }}

  .food-table td {{
    padding: 12px 14px;
    font-size: 10pt;
    line-height: 1.9;
    vertical-align: top;
    background: white;
    border: 0.5px solid #ddd;
  }}

  /* ===== 每日食谱卡片 ===== */
  .day-card {{
    margin-bottom: 14px;
    border: 1px solid #2A6F4D;
    border-radius: 6px;
    overflow: hidden;
    page-break-inside: avoid;
  }}

  .day-header {{
    background: #2A6F4D;
    color: white;
    padding: 9px 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}

  .day-tag {{
    font-size: 12pt;
    font-weight: 700;
  }}

  .day-num {{
    font-family: "Noto Serif CJK SC", serif;
    font-size: 14pt;
    letter-spacing: 1px;
  }}

  .day-week {{
    font-size: 11pt;
    margin-left: 4px;
    opacity: 0.85;
  }}

  .day-theme {{
    font-size: 10.5pt;
    font-style: italic;
    opacity: 0.95;
  }}

  .meal-table {{
    width: 100%;
    border-collapse: collapse;
    background: white;
  }}

  .meal-table td {{
    padding: 9px 12px;
    border-top: 0.5px solid #E5E5E5;
    font-size: 10pt;
    line-height: 1.7;
  }}

  .meal-label {{
    width: 56px;
    background: #E8F1EA;
    color: #F4A261;
    font-weight: 700;
    text-align: center;
    border-right: 0.5px solid #D4D4D4;
  }}

  .meal-content {{
    color: #2C3E2D;
  }}

  .day-tip {{
    background: #FAF3E7;
    border-left: 3px solid #F4A261;
    padding: 8px 14px;
    font-size: 9.5pt;
    color: #555;
  }}

  .tip-icon {{
    margin-right: 4px;
  }}

  /* ===== 实用工具页 ===== */
  .tools-page {{
    page-break-before: always;
  }}

  .portion-table {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 18px;
    border: 1px solid #2A6F4D;
    border-radius: 6px;
    overflow: hidden;
  }}

  .portion-table td {{
    padding: 10px 14px;
    border-top: 0.5px solid #ddd;
    font-size: 10.5pt;
  }}

  .portion-label {{
    background: #E8F1EA;
    color: #2A6F4D;
    font-weight: 700;
    text-align: center;
    width: 100px;
    font-size: 11pt;
  }}

  /* 烹饪窍门列表 */
  .cooking-tips {{
    list-style: none;
    padding: 0;
  }}

  .cooking-tips li {{
    margin-bottom: 10px;
    padding: 10px 14px;
    background: #FAF3E7;
    border-left: 3px solid #52B788;
    font-size: 10pt;
    line-height: 1.7;
  }}

  .cooking-tips li b {{
    color: #F4A261;
    font-size: 10.5pt;
    display: block;
    margin-bottom: 3px;
  }}

  /* 重要提醒 */
  .warning-box {{
    background: #FDF1ED;
    border-left: 4px solid #E76F51;
    padding: 14px 18px;
    margin: 18px 0;
    font-size: 10pt;
    line-height: 1.8;
    color: #8B2E1A;
  }}

  .warning-box b {{
    color: #C0392B;
    font-size: 11pt;
  }}

  .warning-box ul {{
    margin: 6px 0 0 18px;
  }}

  /* 结尾 */
  .ending {{
    text-align: center;
    margin-top: 22px;
    padding: 18px 0;
    border-top: 1px solid #2A6F4D;
    border-bottom: 1px solid #2A6F4D;
  }}

  .ending-line1 {{
    font-size: 11.5pt;
    color: #555;
    margin-bottom: 6px;
  }}

  .ending-line2 {{
    font-size: 13pt;
    font-weight: 700;
    color: #2A6F4D;
    margin-bottom: 10px;
  }}

  .ending-line3 {{
    font-size: 10pt;
    color: #888;
    font-style: italic;
  }}

  .footer-note {{
    text-align: center;
    font-size: 8.5pt;
    color: #aaa;
    margin-top: 14px;
    line-height: 1.6;
  }}
</style>
</head>
<body>

<!-- ========== 封面 ========== -->
<div class="cover">
  <div class="cover-title">7天降脂食谱表</div>
  <div class="cover-subtitle">—— 给查出血管斑块的你和家人 ——</div>
  <div class="cover-band">0 花费 · 在家做 · 中国家庭口味 · 坚持 21 天见效</div>

  <h2 class="section-h1">📖 使用说明</h2>
  <div class="intro-box">
    本食谱表基于 <b>地中海饮食模式</b> 简化制定,适合中国家庭日常烹饪。
    每日总热量约 <b>1600-1800 kcal</b>,适用于成人血脂偏高、轻中度斑块、
    想长期养护血管的人群。
    <br><br>
    <b>三大原则:</b><br>
    ① <b>主食粗细搭配</b> —— 每餐主食一半为糙米 / 燕麦 / 杂粮<br>
    ② <b>优质蛋白优先</b> —— 深海鱼、豆制品、白肉、鸡蛋<br>
    ③ <b>油盐糖严控</b> —— 每日油 ≤25g、盐 ≤5g、添加糖 ≤25g
  </div>

  <h2 class="section-h1">🚦 红绿灯食物清单</h2>
  <table class="food-table">
    <tr>
      <th class="green">✅ 多吃(绿灯)</th>
      <th class="yellow">⚠ 少吃(黄灯)</th>
      <th class="red">❌ 不吃(红灯)</th>
    </tr>
    <tr>
      <td>
        燕麦、糙米、藜麦<br>
        深海鱼、豆腐<br>
        鸡胸、虾、鸡蛋<br>
        西兰花、菠菜、菌菇<br>
        蓝莓、苹果、坚果<br>
        橄榄油、亚麻籽油
      </td>
      <td>
        白米饭、白面条<br>
        瘦红肉(每周 ≤2 次)<br>
        全脂奶、奶酪<br>
        土豆、玉米<br>
        果汁(整果代替)<br>
        酱油、蚝油
      </td>
      <td>
        肥肉、动物内脏<br>
        炸鸡、薯条、蛋糕<br>
        植脂末、人造奶油<br>
        氢化植物油<br>
        含糖饮料、奶茶<br>
        腌制品、加工肉
      </td>
    </tr>
  </table>
</div>

<!-- ========== 7 天食谱 ========== -->
<h2 class="section-h1">🍽 7 天详细食谱</h2>
<p style="color:#888;font-size:10pt;margin-bottom:14px;">
每日三餐 + 加餐,直接照着买、照着做
</p>

{render_meals_html(MEALS)}

<!-- ========== 实用工具页 ========== -->
<div class="tools-page">
  <h2 class="section-h1">🛠 实用工具与小窍门</h2>

  <h3 class="section-h2">📏 一份是多少?手掌就是你的量勺</h3>
  <table class="portion-table">
    <tr><td class="portion-label">✊ 一拳</td><td>约 150g 熟主食(糙米饭 / 杂粮饭)</td></tr>
    <tr><td class="portion-label">🤚 一掌心</td><td>约 80-100g 肉 / 鱼(去掉手指部分)</td></tr>
    <tr><td class="portion-label">👍 一拇指</td><td>约 10-15g 油脂(一勺油 / 一小把坚果)</td></tr>
    <tr><td class="portion-label">🙏 两手捧</td><td>约 250-300g 蔬菜(熟后体积)</td></tr>
  </table>

  <h3 class="section-h2">🍳 5 个降脂烹饪小窍门</h3>
  <ul class="cooking-tips">
    <li><b>1. 把油壶换成喷油壶</b>几块钱一个,每次喷 2 下,一天总油量轻松控制在 25g 内。</li>
    <li><b>2. 蒸 &gt; 煮 &gt; 炒 &gt; 炸</b>优先选蒸和水煮,炒菜时锅热再下油,温度低油烟少。</li>
    <li><b>3. 用葱姜蒜花椒代替一半盐</b>天然香料增鲜,每日盐量降到 5g 以下不痛苦。</li>
    <li><b>4. 焯水后再炒</b>蔬菜先焯 30 秒,可大幅减少炒制时间和用油量。</li>
    <li><b>5. 餐前喝一碗清汤</b>番茄汤 / 紫菜汤先垫底,自然减少正餐摄入约 20%。</li>
  </ul>

  <div class="warning-box">
    <b>⚠ 重要提醒</b><br><br>
    本食谱 <b>不能替代药物治疗</b>。如果你已被医生确诊需要服用他汀类降脂药、
    抗血小板药物,请 <b>务必遵医嘱按时服药</b>,饮食调理是辅助手段。
    <br><br>
    出现以下情况请 <b>立即就医</b>:
    <ul>
      <li>胸闷胸痛持续超过 15 分钟</li>
      <li>一侧肢体麻木无力</li>
      <li>突发剧烈头痛伴呕吐</li>
      <li>言语含糊或视物模糊</li>
    </ul>
  </div>

  <div class="ending">
    <div class="ending-line1">健康从来不是奢侈品,</div>
    <div class="ending-line2">而是日复一日,踏踏实实过日子。</div>
    <div class="ending-line3">—— 愿这份食谱,陪你和家人一起,慢慢把血管养回来。</div>
  </div>

  <p class="footer-note">
    本食谱整理自《中国居民膳食指南(2022)》、地中海饮食研究及临床营养学共识 · 仅供个人参考使用<br>
    © 2026 健康公众号 · 关注我们,每周三获取血管养护干货
  </p>
</div>

</body>
</html>
"""


def main():
    print("正在生成 PDF...")
    HTML(string=HTML_TEMPLATE).write_pdf(OUTPUT_PDF)
    size_kb = Path(OUTPUT_PDF).stat().st_size / 1024
    print(f"✅ 生成成功!")
    print(f"   📄 文件路径:{OUTPUT_PDF}")
    print(f"   📦 文件大小:{size_kb:.1f} KB")


if __name__ == "__main__":
    main()
