# -*- coding: utf-8 -*-
"""
生成《工程伦理与网络安全法》小组汇报 PPTX（16:9）。

用法：
    python scripts/build_pptx.py

产物：仓库根目录下的 工程伦理汇报_第7组.pptx
改文案 / 配色 / 版式都在本文件里改，改完重跑覆盖即可。
"""
import os
import copy

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from lxml import etree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "ppt", "assets", "img")
OUT = os.path.join(ROOT, "工程伦理汇报_第7组.pptx")

SW, SH = Inches(13.333), Inches(7.5)
M = Inches(0.85)                      # 左右页边距
CW = SW - 2 * M                       # 内容区宽度

PAPER = RGBColor(0xFD, 0xFC, 0xF8)
INK = RGBColor(0x0A, 0x0A, 0x0A)
INK2 = RGBColor(0x33, 0x33, 0x33)
INK3 = RGBColor(0x70, 0x70, 0x70)
ACCENT = RGBColor(0x1A, 0x3A, 0x7A)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
RULE = RGBColor(0xCF, 0xCC, 0xC0)

SONG = "宋体"
HEI = "黑体"


# ---------- 基础工具 ----------
def new_deck():
    prs = Presentation()
    prs.slide_width, prs.slide_height = SW, SH
    return prs


def blank(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg = s.background.fill
    bg.solid()
    bg.fore_color.rgb = PAPER
    return s


def set_run_font(run, name, size, bold=False, color=INK):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = etree.SubElement(rPr, qn(tag))
        el.set("typeface", name)


def text_box(slide, x, y, w, h, text, size=18, bold=False, color=INK, font=SONG,
             align=PP_ALIGN.LEFT, spacing=1.35, anchor=MSO_ANCHOR.TOP):
    x, y, w, h = int(x), int(y), int(w), int(h)
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    lines = text.split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        r = p.add_run()
        r.text = line
        set_run_font(r, font, size, bold, color)
    return tb


def rule(slide, x, y, w, color=RULE, weight=1.0):
    x, y, w = int(x), int(y), int(w)
    ln = slide.shapes.add_connector(1, x, y, x + w, y)
    ln.line.color.rgb = color
    ln.line.width = Pt(weight)
    return ln


def card(slide, x, y, w, h, fill=WHITE, line=RULE):
    x, y, w, h = int(x), int(y), int(w), int(h)
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    sh.line.color.rgb = line
    sh.line.width = Pt(0.75)
    sh.shadow.inherit = False
    return sh


def set_alpha(shape, pct):
    """给纯色填充加透明度，pct 为 0-100 的透明百分比。"""
    srgb = shape.fill.fore_color._xFill.find(qn("a:srgbClr"))
    alpha = etree.SubElement(srgb, qn("a:alpha"))
    alpha.set("val", str(int((100 - pct) * 1000)))


def shape_rect(slide, x, y, w, h, fill=None):
    """带取整的矩形，避免小数 EMU 让 PowerPoint 拒绝打开。"""
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, int(x), int(y), int(w), int(h))
    if fill is not None:
        sh.fill.solid()
        sh.fill.fore_color.rgb = fill
        sh.line.fill.background()
    sh.shadow.inherit = False
    return sh


def cover_picture(slide, path):
    """按 16:9 裁切铺满整页，不变形。"""
    from PIL import Image  # python-pptx 依赖 Pillow
    with Image.open(path) as im:
        iw, ih = im.size
    a = iw / ih
    target = SW / SH
    pic = slide.shapes.add_picture(path, 0, 0, width=SW)
    if a < target:      # 图更窄，裁上下
        frac = (1 - (a / target)) / 2
        pic.crop_top = pic.crop_bottom = frac
    else:               # 图更宽，裁左右
        frac = (1 - (target / a)) / 2
        pic.crop_left = pic.crop_right = frac
    pic.left, pic.top, pic.width, pic.height = 0, 0, SW, SH
    return pic


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def transition(slide, effect="fade", speed="med"):
    """给单页加切换动画（python-pptx 没有对应 API，直接写 OOXML）。"""
    sld = slide._element
    for old in sld.findall(qn("p:transition")):
        sld.remove(old)
    tr = etree.SubElement(sld, qn("p:transition"))
    tr.set("spd", speed)
    etree.SubElement(tr, qn("p:" + effect))


def kicker(slide, text, y=Inches(0.62)):
    text_box(slide, M, y, CW, Inches(0.3), text, 12, False, ACCENT, SONG, spacing=1.0)


def title(slide, text, y=Inches(0.98), size=34):
    text_box(slide, M, y, CW, Inches(0.9), text, size, True, INK, HEI, spacing=1.15)


def footer(slide, text):
    text_box(slide, M, SH - Inches(0.62), CW, Inches(0.3), text, 10.5, False, INK3, SONG)


def page_no(slide, n, total):
    text_box(slide, SW - M - Inches(0.9), SH - Inches(0.62), Inches(0.9), Inches(0.3),
             "%d / %d" % (n, total), 10.5, False, INK3, SONG, PP_ALIGN.RIGHT)


# ---------- 各页 ----------
def s01_cover(prs):
    s = blank(prs)
    cover_picture(s, os.path.join(IMG, "night-app.jpg"))
    shade = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SW, SH)
    shade.fill.solid()
    shade.fill.fore_color.rgb = RGBColor(0, 0, 0)
    shade.line.fill.background()
    shade.shadow.inherit = False
    set_alpha(shade, 55)

    text_box(s, M, Inches(4.0), CW, Inches(0.35), "工程伦理与网络安全法 · 小组汇报", 13, False,
             RGBColor(0xE8, 0xE6, 0xDE), SONG, spacing=1.0)
    text_box(s, M, Inches(4.45), Inches(9.5), Inches(1.9),
             "数据从哪里来\n滴滴网络安全审查案", 46, True, WHITE, HEI, spacing=1.15)
    text_box(s, M, Inches(6.25), Inches(9.0), Inches(0.5),
             "80.26 亿元罚款，647.09 亿条个人信息，七年时间。这条采集链是从功能需求里长出来的。",
             14, False, RGBColor(0xE8, 0xE6, 0xDE), SONG, spacing=1.3)
    text_box(s, M, Inches(6.78), Inches(9.0), Inches(0.35),
             "第 7 组　刘昊阳　刘科阳　鲁瑜　彭超　彭真昕", 12, False,
             RGBColor(0xE8, 0xE6, 0xDE), SONG, spacing=1.0)
    notes(s, "开场先看这张照片：夜里跑在路上的网约车，和车里的这块屏幕。案子起点在这个屏幕上，不在法律条文里。")


def s02_numbers(prs):
    s = blank(prs)
    kicker(s, "三个数字")
    title(s, "这一案留下了三个数字")
    data = [("80.26", "亿", "罚款（元）"), ("647", "亿条", "违法处理的个人信息"), ("7", "年", "违法行为持续时间")]
    w = CW / 3
    for i, (num, unit, cap) in enumerate(data):
        x = M + i * w
        tb = s.shapes.add_textbox(int(x), Inches(2.5), int(w - Inches(0.2)), Inches(1.2))
        tf = tb.text_frame
        tf.word_wrap = False
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        r1 = p.add_run()
        r1.text = num
        set_run_font(r1, HEI, 62, True, INK)
        r2 = p.add_run()
        r2.text = " " + unit
        set_run_font(r2, HEI, 20, True, ACCENT)
        text_box(s, x, Inches(3.75), w - Inches(0.3), Inches(0.4), cap, 14, False, INK3, SONG)
    rule(s, M, Inches(3.55), CW)
    text_box(s, M, Inches(4.4), Inches(9.6), Inches(0.9),
             "16 项事实，8 个方面，持续 7 年。", 20, False, INK2, SONG, spacing=1.4)
    footer(s, "数据来源：国家互联网信息办公室答记者问")
    page_no(s, 2, 16)
    notes(s, "先给三个数字建立量级感。80 亿是结果，647 亿条和 7 年是原因。注意 647 亿条说的是「违法处理」，不只是「收集」。")


def s03_timeline(prs):
    s = blank(prs)
    kicker(s, "Timeline")
    title(s, "从成立到处罚，九年半")
    y = Inches(2.75)
    x0, x1 = M, SW - M
    ln = s.shapes.add_connector(1, x0, y, x1, y)
    ln.line.color.rgb = INK
    ln.line.width = Pt(1.2)

    nodes = [("2013.01", "公司成立", "网约车、顺风车、两轮车"),
             ("2015.06", "违法行为起点", "处罚决定认定的最早时间"),
             ("2021.07", "审查与下架", "7 月 2 日审查，7 月 4 日下架"),
             ("2022.07", "处罚公布", "80.26 亿元，高管各 100 万"),
             ("2022 后", "整改与退市", "全面自查，退出美股")]
    for i, (yr, h4, p) in enumerate(nodes):
        cx = x0 + (x1 - x0) * (i + 0.5) / 5
        dot = s.shapes.add_shape(MSO_SHAPE.OVAL, int(cx - Inches(0.09)), int(y - Inches(0.09)),
                                 Inches(0.18), Inches(0.18))
        dot.fill.solid(); dot.fill.fore_color.rgb = ACCENT
        dot.line.color.rgb = PAPER; dot.line.width = Pt(2); dot.shadow.inherit = False
        text_box(s, int(cx - Inches(1.1)), y - Inches(0.78), Inches(2.2), Inches(0.3), yr, 11,
                 True, INK3, SONG, PP_ALIGN.CENTER)
        text_box(s, int(cx - Inches(1.1)), y + Inches(0.28), Inches(2.2), Inches(0.35), h4, 14,
                 True, INK, HEI, PP_ALIGN.CENTER)
        text_box(s, int(cx - Inches(1.1)), y + Inches(0.66), Inches(2.2), Inches(0.6), p, 10,
                 False, INK2, SONG, PP_ALIGN.CENTER, spacing=1.25)

    # 法律生效轴
    ly = Inches(5.05)
    rule(s, x0, ly, x1 - x0, RULE, 0.75)
    text_box(s, x0, ly - Inches(0.32), Inches(1.2), Inches(0.28), "法律生效", 10, False, INK3, SONG)
    lx = x0 + (x1 - x0) * 0.56
    d2 = s.shapes.add_shape(MSO_SHAPE.OVAL, int(lx - Inches(0.06)), int(ly - Inches(0.06)), Inches(0.12), Inches(0.12))
    d2.fill.solid(); d2.fill.fore_color.rgb = ACCENT; d2.line.fill.background(); d2.shadow.inherit = False
    text_box(s, lx - Inches(1.55), ly + Inches(0.16), Inches(3.1), Inches(0.3),
             "《数据安全法》2021-09-01 施行", 11, True, INK, HEI, PP_ALIGN.CENTER)
    text_box(s, lx - Inches(1.55), ly + Inches(0.46), Inches(3.1), Inches(0.3),
             "《个人信息保护法》2021-11-01 施行", 10.5, False, INK3, SONG, PP_ALIGN.CENTER)

    text_box(s, M, Inches(5.95), CW, Inches(0.6),
             "违法从 2015 年 6 月开始，两部新法 2021 年秋天才施行。同一套做法，在法条落地之后变成了违法。",
             13, False, INK2, SONG, spacing=1.35)
    footer(s, "数据来源：网信办公告与答记者问")
    page_no(s, 3, 16)
    notes(s, "看这条线上的两个错位：违法从 2015 年开始，但《数据安全法》2021 年 9 月才施行，"
             "《个人信息保护法》2021 年 11 月才施行。三法能并罚，是因为行为一直持续到新法生效之后。")


def s04_story_a(prs):
    s = blank(prs)
    kicker(s, "Case · 2013–2021")
    title(s, "业务扩张与数据积累")

    col_w = Inches(6.1)
    blocks = [("打车靠匹配",
               "一笔订单要在几秒内派给最合适的司机，判断越准，成交率越高，要发的补贴越少。"
               "数据采集因此从辅助功能变成了核心能力。"),
              ("业务线一多，权限就宽",
               "到 2021 年，境内 41 款 App 共用一套账号、支付、定位与画像体系。相册用来看行程凭证，"
               "剪切板用来识别口令，应用列表用来判断用户装没装竞品。"),
              ("单看都有理由",
               "每一项在当时都能在需求文档里找到依据，问题在于没有人核算总量。")]
    y = Inches(1.95)
    for h4, p in blocks:
        text_box(s, M, y, col_w, Inches(0.32), h4, 15, True, INK, HEI)
        text_box(s, M, y + Inches(0.34), col_w, Inches(0.9), p, 13, False, INK2, SONG, spacing=1.45)
        y += Inches(1.42)

    pic_x = SW - M - Inches(5.0)
    s.shapes.add_picture(os.path.join(IMG, "didi-office.jpg"), pic_x, Inches(1.95), width=Inches(5.0))
    text_box(s, pic_x, Inches(4.75), Inches(5.0), Inches(0.5),
             "滴滴位于北京中关村数字山谷的办公楼（室内设计项目实景）", 9.5, False, INK3, SONG, spacing=1.3)

    footer(s, "2013–2021：从 0 到 41 款 App")
    page_no(s, 4, 16)
    notes(s, "这一段讲起因，不用念数字。要讲清三件事：打车靠匹配，匹配靠数据；业务线一多，权限就跟着膨胀；"
             "每一项在当时都有理由，问题是没人做总账。")


def s05_story_b(prs):
    s = blank(prs)
    kicker(s, "Case · 2021–2022")
    title(s, "2021 年 7 月：上市、审查、下架")

    col_w = Inches(6.9)
    blocks = [("6 月 30 日 – 7 月 4 日",
               "6 月 30 日上市；7 月 2 日，网络安全审查办公室宣布启动审查，审查期间停止新用户注册；"
               "7 月 4 日，网信办通报 App 严重违法违规收集使用个人信息，通知下架。"),
              ("此后一年",
               "7 月中旬多部门联合进驻。新用户注册停了一年，12 月宣布启动从纽交所退市，2022 年 6 月完成。"),
              ("2022 年 7 月 21 日",
               "处罚决定公布：罚款 80.26 亿元，程维、柳青各 100 万元。")]
    y = Inches(1.95)
    for h4, p in blocks:
        text_box(s, M, y, col_w, Inches(0.3), h4, 14, True, ACCENT, HEI)
        text_box(s, M, y + Inches(0.32), col_w, Inches(1.0), p, 12.5, False, INK2, SONG, spacing=1.45)
        y += Inches(1.5)

    qx = SW - M - Inches(4.6)
    box = card(s, qx, Inches(1.95), Inches(4.6), Inches(3.5), RGBColor(0xF5, 0xF3, 0xEA))
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, qx, Inches(1.95), Inches(0.05), Inches(3.5))
    bar.fill.solid(); bar.fill.fore_color.rgb = ACCENT; bar.line.fill.background(); bar.shadow.inherit = False
    text_box(s, qx + Inches(0.28), Inches(2.15), Inches(4.05), Inches(2.7),
             "「为防范国家数据安全风险，维护国家安全，保障公共利益……对『滴滴出行』实施网络安全审查，"
             "审查期间『滴滴出行』停止新用户注册。」", 12, False, INK2, SONG, spacing=1.5)
    text_box(s, qx + Inches(0.28), Inches(4.9), Inches(4.05), Inches(0.4),
             "—— 网络安全审查办公室公告，2021-07-02", 9.5, False, INK3, SONG)

    footer(s, "2021.6–2022.7：上市、审查、下架、处罚")
    page_no(s, 5, 16)
    notes(s, "这一段是事件主体，按日期讲，别打乱顺序。重点在两个转折：一是上市四天后就被审查，"
             "二是下架之后新用户停了一年。处罚是最后一步，不是全部。")


def s06_chart(prs):
    s = blank(prs)
    kicker(s, "Data · 16 项事实")
    title(s, "采集量分布")

    bg = card(s, M, Inches(1.85), CW, Inches(4.75))
    import math
    rows = [("出行意图分析", 539.76), ("剪切板 / 应用列表", 83.23), ("常驻城市", 15.38),
            ("异地商务 / 旅游", 3.04), ("精准位置", 1.67), ("「家」与「公司」地址", 1.53),
            ("人脸识别", 1.07)]
    left = M + Inches(2.45)
    width_max = CW - Inches(2.45) - Inches(1.6)
    top = Inches(2.1)
    step = Inches(0.48)
    lo, hi = math.log10(0.1), math.log10(1000)

    for i, (label, v) in enumerate(rows):
        yy = top + i * step
        text_box(s, M + Inches(0.25), yy - Inches(0.02), Inches(2.1), Inches(0.3), label, 11,
                 False, INK, SONG, PP_ALIGN.RIGHT)
        wfrac = (math.log10(v) - lo) / (hi - lo)
        w = int(width_max * wfrac)
        bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, yy + Inches(0.04), Emu(w), Inches(0.24))
        bar.fill.solid(); bar.fill.fore_color.rgb = ACCENT
        bar.line.fill.background(); bar.shadow.inherit = False
        text_box(s, left + Emu(w) + Inches(0.12), yy - Inches(0.02), Inches(1.3), Inches(0.3),
                 ("%.2f 亿条" % v), 10.5, False, INK2, SONG)

    # 刻度说明
    for lab, frac in (("0.1 亿", 0), ("1 亿", 0.25), ("10 亿", 0.5), ("100 亿", 0.75), ("1000 亿", 1)):
        xx = left + int(width_max * frac)
        text_box(s, xx - Inches(0.4), top + len(rows) * step + Inches(0.05), Inches(0.8), Inches(0.25),
                 lab, 9, False, INK3, SONG, PP_ALIGN.CENTER)
    text_box(s, M + Inches(0.25), top + len(rows) * step + Inches(0.35), CW - Inches(0.5), Inches(0.3),
             "横轴为对数刻度；数据来自网信办答记者问", 9.5, False, INK3, SONG)

    footer(s, "16 项事实中的 7 项")
    page_no(s, 6, 16)
    notes(s, "用对数刻度是因为差了三个数量级。重点看两条：出行意图 539 亿条，是给用户贴标签用的；"
             "人脸识别 1.07 亿条，属于敏感信息。两项都不是打车的必要条件。")


def s07_engineering(prs):
    s = blank(prs)
    kicker(s, "Engineering view")
    title(s, "违规是怎么发生的")
    items = [("相册截图", "需求叫「上传行程凭证」，实现只有几行权限申请。相册里的聊天记录、证件照、"
                          "银行短信一起进了服务器。1196.39 万条。"),
             ("剪切板与应用列表", "写进 SDK，每次启动自动执行。识别口令、判断竞品，和打车无关。83.23 亿条。"),
             ("明文存身份证号", "收集有正当性，存储方式没有。5780.26 万条明文，拖库就收不回来。"),
             ("频繁索取无关权限", "顺风车场景反复要「电话权限」。权限清单和功能清单对不上。")]
    cw, ch = (CW - Inches(0.5)) / 2, Inches(1.75)
    for i, (h4, p) in enumerate(items):
        x = M + (i % 2) * (cw + Inches(0.5))
        y = Inches(1.95) + (i // 2) * (ch + Inches(0.4))
        card(s, x, y, cw, ch)
        top = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, int(x), int(y), int(cw), Inches(0.045))
        top.fill.solid(); top.fill.fore_color.rgb = ACCENT; top.line.fill.background(); top.shadow.inherit = False
        text_box(s, x + Inches(0.3), y + Inches(0.28), cw - Inches(0.6), Inches(0.32), h4, 15, True, INK, HEI)
        text_box(s, x + Inches(0.3), y + Inches(0.7), cw - Inches(0.6), Inches(0.85), p, 11.5, False, INK2, SONG,
                 spacing=1.4)
    footer(s, "默认值由工程师设定")
    page_no(s, 7, 16)
    notes(s, "这页是全场技术核心。四个动作单看都能在需求文档里找到理由，叠起来就是系统性违规。"
             "而且它们大多是默认开启的——默认值是谁写的？工程师。所以责任不能只推给产品经理。")


def s08_facts(prs):
    s = blank(prs)
    kicker(s, "Evidence · 官方怎么说的")
    title(s, "16 项违法事实")

    pic_w = Inches(5.3)
    s.shapes.add_picture(os.path.join(IMG, "report-post.jpg"), M, Inches(1.95), width=pic_w)
    text_box(s, M, Inches(1.95) + int(pic_w * 0.7) + Inches(0.08), pic_w, Inches(0.4),
             "人民网微博通报：16 项违法事实，归纳为 8 个方面", 9.5, False, INK3, SONG, spacing=1.3)

    facts = ["① 违法收集相册截图　1196.39 万条",
             "② 过度收集剪切板、应用列表　83.23 亿条",
             "③ 过度收集人脸识别　1.07 亿条",
             "④ 精准位置（含后台运行）　1.67 亿条",
             "⑤ 司机身份证号明文存储　5780.26 万条"]
    x = M + pic_w + Inches(0.55)
    y = Inches(2.0)
    for f in facts:
        text_box(s, x, y, SW - x - M, Inches(0.42), f, 13, False, INK2, SONG, spacing=1.4)
        y += Inches(0.62)
    footer(s, "图片来源：人民网官方微博")
    page_no(s, 8, 16)
    notes(s, "这页不放我的转述，直接放人民网的通报截图，旁边列出五项关键事实。"
             "用意是：这些数字是监管机关认定的，不是我们的推断。")


def s09_penalty(prs):
    s = blank(prs)
    kicker(s, "Penalty · 处罚长什么样")
    title(s, "「事实清楚、证据确凿、情节严重、性质恶劣」", size=26)

    pic_w = Inches(5.5)
    s.shapes.add_picture(os.path.join(IMG, "penalty-notice.jpg"), M, Inches(2.0), width=pic_w)
    text_box(s, M, Inches(2.0) + int(pic_w * 0.59) + Inches(0.08), pic_w, Inches(0.4),
             "「网信中国」发布的处罚决定（2022 年 7 月 21 日）", 9.5, False, INK3, SONG, spacing=1.3)

    qx = M + pic_w + Inches(0.55)
    qw = SW - qx - M
    card(s, qx, Inches(2.0), qw, Inches(3.2), RGBColor(0xF5, 0xF3, 0xEA))
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, qx, Inches(2.0), Inches(0.05), Inches(3.2))
    bar.fill.solid(); bar.fill.fore_color.rgb = ACCENT; bar.line.fill.background(); bar.shadow.inherit = False
    text_box(s, qx + Inches(0.3), Inches(2.25), qw - Inches(0.6), Inches(2.4),
             "依据《网络安全法》《数据安全法》《个人信息保护法》《行政处罚法》等法律法规，"
             "对滴滴全球股份有限公司处人民币 80.26 亿元罚款，对董事长兼 CEO 程维、"
             "总裁柳青各处人民币 100 万元罚款。", 12.5, False, INK2, SONG, spacing=1.5)
    text_box(s, qx + Inches(0.3), Inches(4.55), qw - Inches(0.6), Inches(0.4),
             "—— 国家互联网信息办公室处罚决定", 9.5, False, INK3, SONG)
    footer(s, "依据四部法律")
    page_no(s, 9, 16)
    notes(s, "注意依据是四部法律：三法加行政处罚法。并罚容易被讲成重复处罚，其实是三种法益各自被侵犯。")


def s10_law(prs):
    s = blank(prs)
    kicker(s, "Legal basis · 三部法律各管一段")
    title(s, "法律依据")

    cards = [("网络安全法", "收个人信息要合法、正当、必要",
              "第 41 条　收集使用个人信息的原则\n第 21 条　等级保护\n第 42 条　不得泄露",
              "本案：剪切板与应用列表 83.23 亿条、相册截图 1196.39 万条，超出必要范围。"),
             ("数据安全法", "数据处理不得危害国家安全",
              "第 27 条　数据安全管理制度\n第 36 条　向境外提供数据的限制",
              "本案：审查认定存在严重影响国家安全的数据处理活动，细节依法不公开。"),
             ("个人信息保护法", "最小必要、告知目的、敏感信息单独同意",
              "第 6 条　最小必要\n第 17 条　告知义务\n第 28 条　敏感个人信息",
              "本案：未告知即分析出行意图 539.76 亿条；人脸 1.07 亿条、身份证号 5780.26 万条。")]
    cw = (CW - Inches(0.6)) / 3
    for i, (law, req, arts, case) in enumerate(cards):
        x = M + i * (cw + Inches(0.3))
        card(s, x, Inches(1.9), cw, Inches(3.95))
        text_box(s, x + Inches(0.26), Inches(2.1), cw - Inches(0.5), Inches(0.3), law, 10.5, False, INK3, SONG)
        text_box(s, x + Inches(0.26), Inches(2.42), cw - Inches(0.5), Inches(0.9), req, 12.5, True, INK, HEI,
                 spacing=1.3)
        text_box(s, x + Inches(0.26), Inches(3.45), cw - Inches(0.5), Inches(0.95), arts, 9.5, False, INK2, SONG,
                 spacing=1.4)
        rule(s, x + Inches(0.26), Inches(4.45), cw - Inches(0.52), RULE, 0.75)
        text_box(s, x + Inches(0.26), Inches(4.55), cw - Inches(0.5), Inches(1.1), case, 9, False, INK3, SONG,
                 spacing=1.4)

    text_box(s, M, Inches(5.95), CW, Inches(0.6),
             "三条法各管一层：网络运行秩序、数据安全、个人权益。三层同时被突破，处罚就落三次，"
             "罚的是三种不同的违法后果。", 12, False, INK2, SONG, spacing=1.4)
    footer(s, "条文以现行有效版本为准")
    page_no(s, 10, 16)
    notes(s, "这页回答「为什么罚三次」。讲的时候不要念条号，先把每张卡的第一句话讲出来——"
             "收信息要必要、数据不能危害国家安全、个人信息要告知和单独同意，然后再指下面那行「本案」。")


def s11_enforcement(prs):
    s = blank(prs)
    kicker(s, "Enforcement · 两道程序")
    title(s, "监管程序")

    steps = [("1", "网络安全审查", "依《国家安全法》《网络安全法》《网络安全审查办法》，查数据处理是否影响国家安全。"),
             ("2", "立案调查", "调查询问、技术取证、听取企业意见。"),
             ("3", "行政处罚", "三法并罚，企业与主管人员同时追责。"),
             ("4", "整改与退市", "全面自查；上市不足一年即启动退市。")]
    y = Inches(1.95)
    for no, h4, p in steps:
        c = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, M, y, Inches(0.42), Inches(0.42))
        c.fill.solid(); c.fill.fore_color.rgb = PAPER
        c.line.color.rgb = INK; c.line.width = Pt(1); c.shadow.inherit = False
        tf = c.text_frame; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        pr = tf.paragraphs[0]; pr.alignment = PP_ALIGN.CENTER
        r = pr.add_run(); r.text = no; set_run_font(r, HEI, 13, True, INK)
        text_box(s, M + Inches(0.62), y - Inches(0.02), Inches(5.2), Inches(0.3), h4, 14, True, INK, HEI)
        text_box(s, M + Inches(0.62), y + Inches(0.32), Inches(5.2), Inches(0.7), p, 11, False, INK2, SONG,
                 spacing=1.35)
        y += Inches(1.22)

    qx = M + Inches(6.3)
    qw = SW - qx - M
    card(s, qx, Inches(1.95), qw, Inches(4.0), RGBColor(0xF5, 0xF3, 0xEA))
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, qx, Inches(1.95), Inches(0.05), Inches(4.0))
    bar.fill.solid(); bar.fill.fore_color.rgb = ACCENT; bar.line.fill.background(); bar.shadow.inherit = False
    text_box(s, qx + Inches(0.3), Inches(2.2), qw - Inches(0.6), Inches(3.0),
             "「网络安全审查还发现，滴滴公司存在严重影响国家安全的数据处理活动，以及拒不履行监管部门的"
             "明确要求、阳奉阴违、恶意逃避监管等其他违法违规问题。因涉及国家安全，依法不公开。」",
             12, False, INK2, SONG, spacing=1.5)
    text_box(s, qx + Inches(0.3), Inches(5.35), qw - Inches(0.6), Inches(0.4),
             "—— 网信办答记者问，2022-07-21", 9.5, False, INK3, SONG)

    footer(s, "审查与处罚是两道程序")
    page_no(s, 11, 16)
    notes(s, "很多人只记得 80 亿，不知道前面还有一道网络安全审查。审查看的是国家安全，不公开；"
             "处罚看的是三法义务，公开。两道程序，两套逻辑。")


def s12_ethics(prs):
    s = blank(prs)
    kicker(s, "Ethics")
    title(s, "伦理分析")

    items = [("功利主义", "总收益真的更大吗", "收益在财报，代价分摊到几亿人。两边不在一个账本上，加总算出的总量并不成立。",
              "本案：出行意图 539.76 亿条，换来更准的推荐与更少的补贴。"),
             ("义务论", "「同意」是真的同意吗", "隐私政策几十页，权限与功能捆绑，不点就用不了。这次点击更接近形式。",
              "本案：41 款 App 共用一套授权流程。"),
             ("责任伦理", "一行代码的七年", "后果在时间上滞后、空间上分散，判断不能只看当下好不好用。",
              "本案：「读取剪切板」写进 SDK，七年后是 83.23 亿条。"),
             ("分配正义", "谁承担风险", "罗尔斯的差异原则要求制度安排改善最不利者的处境。",
              "本案：数据用户产、收益归平台、风险留用户。")]
    cw, ch = (CW - Inches(0.5)) / 2, Inches(2.15)
    for i, (eyebrow, h4, p, anchor) in enumerate(items):
        x = M + (i % 2) * (cw + Inches(0.5))
        y = Inches(1.85) + (i // 2) * (ch + Inches(0.3))
        card(s, x, y, cw, ch)
        text_box(s, x + Inches(0.28), y + Inches(0.2), cw - Inches(0.56), Inches(0.28), eyebrow, 10, False, INK3, SONG)
        text_box(s, x + Inches(0.28), y + Inches(0.5), cw - Inches(0.56), Inches(0.35), h4, 14, True, INK, HEI)
        text_box(s, x + Inches(0.28), y + Inches(0.9), cw - Inches(0.56), Inches(0.7), p, 10.5, False, INK2, SONG,
                 spacing=1.35)
        rule(s, x + Inches(0.28), y + Inches(1.6), cw - Inches(0.56), RULE, 0.75)
        text_box(s, x + Inches(0.28), y + Inches(1.68), cw - Inches(0.56), Inches(0.4), anchor, 9, False, INK3, SONG,
                 spacing=1.3)
    footer(s, "四种框架的局限")
    page_no(s, 12, 16)
    notes(s, "四种视角不必都同意，但要各自自洽。每格下面那行「本案」是关键——把框架落到这个案子的具体事实上，"
             "否则就是背概念。")


def s13_takeaways(prs):
    s = blank(prs)
    kicker(s, "Takeaways")
    title(s, "启示")

    items = [("01", "「能做」不等于「该做」", "相册权限能申请，但相册里没有行程单。能力存在，不等于使用正当。"),
             ("02", "合规前置到设计阶段", "最小必要在需求评审时就能判断：这个功能最少要哪些数据，多要的砍掉。"),
             ("03", "组织里要有说「不」的通道", "处罚决定的原话是「阳奉阴违、恶意逃避监管」，指向的是组织执行方式。"),
             ("04", "法律边界就是产品边界", "三法在 2021 年补齐，2015 年开始的做法立刻变成违法。边界会移动。")]
    y = Inches(1.9)
    for no, h4, p in items:
        text_box(s, M, y + Inches(0.05), Inches(0.8), Inches(0.4), no, 16, True, ACCENT, HEI)
        text_box(s, M + Inches(0.8), y, Inches(8.6), Inches(0.35), h4, 14.5, True, INK, HEI)
        text_box(s, M + Inches(0.8), y + Inches(0.36), Inches(10.6), Inches(0.5), p, 11, False, INK2, SONG,
                 spacing=1.3)
        rule(s, M, y + Inches(0.95), CW, RULE, 0.75)
        y += Inches(1.15)
    footer(s, "对工程从业者的建议")
    page_no(s, 13, 16)
    notes(s, "这四条是我们组的总结。第一条最难，因为「能做」的诱惑每天都在；第四条最省钱——法律变了，"
             "产品边界跟着变。")


def s14_summary(prs):
    s = blank(prs)
    kicker(s, "Conclusion")
    title(s, "小结")

    items = [("1", "七年、16 项、647 亿条：规模本身就是结论", "不存在某一处「写错了」，这是一套长期运行、无人复核的默认设置。"),
             ("2", "组织问题，技术补不上", "合规没有否决权，评估排在上线之后，违规只是时间问题。"),
             ("3", "法律在 2021 年补齐，旧做法立刻失效", "产品边界跟着法条移动，早一步算进需求，比事后补便宜得多。")]
    y = Inches(2.0)
    for no, h4, p in items:
        c = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, M, y, Inches(0.5), Inches(0.5))
        c.fill.solid(); c.fill.fore_color.rgb = PAPER
        c.line.color.rgb = INK; c.line.width = Pt(1); c.shadow.inherit = False
        tf = c.text_frame; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        pr = tf.paragraphs[0]; pr.alignment = PP_ALIGN.CENTER
        r = pr.add_run(); r.text = no; set_run_font(r, HEI, 15, True, INK)
        text_box(s, M + Inches(0.75), y - Inches(0.02), CW - Inches(0.8), Inches(0.4), h4, 15, True, INK, HEI)
        text_box(s, M + Inches(0.75), y + Inches(0.45), CW - Inches(0.8), Inches(0.5), p, 11, False, INK2, SONG,
                 spacing=1.35)
        y += Inches(1.5)
    footer(s, "三条结论")
    page_no(s, 14, 16)
    notes(s, "小结收三句：第一句说规模，第二句说组织，第三句说时间。这三句可以脱离 PPT 单独讲，"
             "也是我们这份报告的核心结论。")


def s15_questions(prs):
    s = blank(prs)
    kicker(s, "Discussion")
    title(s, "思考题")

    qs = [("01", "产品经理要读取剪切板提升推荐，说这是行业通行做法。你怎么判断、怎么行动？",
           "提示：区分「功能需要」与「转化率需要」。"),
          ("02", "点「同意」等于同意一切吗？一揽子同意为何难构成有效同意？",
           "提示：最小必要、单独同意、敏感信息。"),
          ("03", "企业罚 80 亿、个人各罚 100 万，合理吗？你会怎么改？",
           "提示：个人罚款额低，但追责信号强。")]
    cw = (CW - Inches(0.6)) / 3
    for i, (no, q, hint) in enumerate(qs):
        x = M + i * (cw + Inches(0.3))
        card(s, x, Inches(1.95), cw, Inches(3.3))
        text_box(s, x + Inches(0.28), Inches(2.15), cw - Inches(0.56), Inches(0.4), no, 16, True, ACCENT, HEI)
        text_box(s, x + Inches(0.28), Inches(2.62), cw - Inches(0.56), Inches(1.6), q, 12, False, INK2, SONG,
                 spacing=1.45)
        rule(s, x + Inches(0.28), Inches(4.35), cw - Inches(0.56), RULE, 0.75)
        text_box(s, x + Inches(0.28), Inches(4.43), cw - Inches(0.56), Inches(0.6), hint, 9.5, False, INK3, SONG,
                 spacing=1.3)
    footer(s, "留三分钟讨论")
    page_no(s, 15, 16)
    notes(s, "收尾。三个问题里第三个最有争议，可以引导到「个人罚款低但信号强」这个角度。")


def s16_thanks(prs):
    s = blank(prs)
    text_box(s, M, Inches(1.6), CW, Inches(0.35), "Q & A", 12, False, ACCENT, SONG, PP_ALIGN.CENTER)
    text_box(s, M, Inches(2.05), CW, Inches(1.6), "谢谢", 72, True, INK, HEI, PP_ALIGN.CENTER, spacing=1.0)
    text_box(s, M, Inches(4.1), CW, Inches(0.4),
             "第 7 组　刘昊阳　刘科阳　鲁瑜　彭超　彭真昕", 13, False, INK2, SONG, PP_ALIGN.CENTER)
    text_box(s, Inches(1.6), Inches(4.75), SW - Inches(3.2), Inches(1.1),
             "资料来源：国家互联网信息办公室处罚决定与答记者问（2022-07-21）；网络安全审查办公室对滴滴启动审查的"
             "公告（2021-07-02）；下架「滴滴出行」App 的通报（2021-07-04）。图片来自人民网官方微博、"
             "网信中国公众号及公开资料。", 9.5, False, INK3, SONG, PP_ALIGN.CENTER, spacing=1.5)
    footer(s, "第 7 组 · 工程伦理与网络安全法")
    page_no(s, 16, 16)
    notes(s, "结尾留在这里，不急着关页面。所有事实出自网信办公开文件，现场可以给出链接核对。欢迎提问。")


def main():
    prs = new_deck()
    for fn in (s01_cover, s02_numbers, s03_timeline, s04_story_a, s05_story_b, s06_chart,
               s07_engineering, s08_facts, s09_penalty, s10_law, s11_enforcement, s12_ethics,
               s13_takeaways, s14_summary, s15_questions, s16_thanks):
        fn(prs)
    for slide in prs.slides:
        transition(slide, "fade", "med")
    prs.save(OUT)
    print("saved:", OUT, os.path.getsize(OUT), "bytes", len(prs.slides.__iter__.__self__._sldIdLst), "slides")


if __name__ == "__main__":
    main()
