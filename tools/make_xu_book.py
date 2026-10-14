#!/usr/bin/env python3
"""把「医藏」体底稿整理为仓库格式：医学源流论 / 伤寒类方 / 洄溪医案 / 慎疾刍言。

用法:
    python3 tools/make_xu_book.py <book> <输入txt> <输出目录>
    book ∈ {yixue, shanghan, huixi, shenji}

输入文本属现代转录，仅作录入底稿；正式文本须与影印底本逐段核对。
"""

import pathlib
import re
import sys

SHIWEN = "<!--文献考辨：本篇属于徐灵胎身后汇刻，多为手稿、门人整理辑录，非作者生前定稿，底本取自光绪十六种刻本，仅供研读参考-->"
NOTE = "<!-- 录入底稿：网络「医藏」电子校点本，属现代转录；本篇尚未逐段比对影印件，标记为待核 -->"

BASE = {
    "yixue": ("医学源流论", "<!-- 底本：清乾隆二十二年（1757）半松斋刻本，见国学大师网 gj-734324pa -->"),
    "shanghan": ("伤寒类方", "<!-- 底本：乾隆半松斋刻本（待补）；现用徐氏醫書系统影印本暂代 -->"),
    "huixi": ("洄溪医案", "<!-- 底本：待取咸丰七年蒋氏衍芬草堂刻本（王孟英校刊） -->"),
    "shenji": ("慎疾刍言", "<!-- 底本：清光绪刻本《徐氏醫書十六種》 -->"),
}


def clean(line: str) -> str:
    return line.replace("\u3000", "").replace("\ufeff", "").strip()


def load(path: str):
    text = pathlib.Path(path).read_text(encoding="utf-8", errors="ignore")
    return [l for l in (clean(x) for x in text.splitlines()) if l]


def header(book_key: str, filename: str) -> str:
    book, di = BASE[book_key]
    out = f"<!-- 文件路径：{book}/{filename} -->\n{di}\n"
    if book_key in ("huixi", "shenji"):
        out += SHIWEN + "\n"
    return out + NOTE


def write(outdir, book_key, filename, body):
    book = BASE[book_key][0]
    text = header(book_key, filename) + f"\n\n# {book}\n\n{body}".rstrip() + "\n"
    (outdir / filename).write_text(text, encoding="utf-8")
    print("wrote", filename, len(text), "chars")


def idx(lines, pred):
    return next((i for i, l in enumerate(lines) if pred(l)), -1)


# ---------- 医学源流论 ----------
def build_yixue(lines, out):
    i_seq = idx(lines, lambda l: l == "自叙")
    i_s = idx(lines, lambda l: l.startswith("卷上"))
    write(out, "yixue", "自叙.md", "## 自叙\n\n" + "\n".join(lines[i_seq + 1 : i_s]) + "\n")

    marks = [(i, l) for i, l in enumerate(lines) if re.match(r"^卷[上下]", l)]
    for juan, fn in (("卷上", "卷上.md"), ("卷下", "卷下.md")):
        body = [f"## {juan}", ""]
        last_cat = None
        for k, (i, l) in enumerate(marks):
            if l[:2] != juan:
                continue
            cat = l[2:]
            end = marks[k + 1][0] if k + 1 < len(marks) else len(lines)
            title = lines[i + 1] if i + 1 < len(lines) else ""
            chunk = lines[i + 2 : end]
            if cat and cat != last_cat:
                body += [f"### {cat}", ""]
                last_cat = cat
            body += [f"#### {title}", "", "\n".join(chunk), ""]
        write(out, "yixue", fn, "\n".join(body) + "\n")


# ---------- 伤寒类方 ----------
def build_shanghan(lines, out):
    marks = [(i, l) for i, l in enumerate(lines) if re.match(r"^卷[一二三四五六七八九十]", l)]
    body = ["## 正文", ""]
    cur_juan = None
    cur_lei = None
    for k, (i, l) in enumerate(marks):
        m = re.match(r"^(卷[一二三四五六七八九十]+)(.*)$", l)
        juan, rest = m.group(1), m.group(2)
        end = marks[k + 1][0] if k + 1 < len(marks) else len(lines)
        if not rest:  # 形如「卷三」，类名在下一行
            rest = lines[i + 1] if i + 1 < len(lines) else ""
            name = lines[i + 2] if i + 2 < len(lines) else ""
            chunk = lines[i + 3 : end]
        else:
            name = lines[i + 1] if i + 1 < len(lines) else ""
            chunk = lines[i + 2 : end]
        lei = re.sub(r"·[一二三四五六七八九十]+$", "", rest)
        if juan != cur_juan:
            body += [f"## {juan}", ""]
            cur_juan = juan
            cur_lei = None
        if lei != cur_lei:
            body += [f"### {lei}", ""]
            cur_lei = lei
        body += [f"#### {name}", "", "\n".join(chunk), ""]
    write(out, "shanghan", "正文.md", "\n".join(body) + "\n")


# ---------- 洄溪医案 ----------
def build_huixi(lines, out):
    i_seq = idx(lines, lambda l: l == "序")
    short = lambda l: len(l.replace(" ", "")) <= 6 and not re.search(r"[，。：；？！]", l)
    i_cat = next(i for i in range(i_seq + 1, len(lines)) if short(lines[i]))

    write(out, "huixi", "自序.md", "## 序\n\n" + "\n".join(lines[i_seq + 1 : i_cat]) + "\n")

    body = ["## 正文", ""]
    marks = [(i, l) for i, l in enumerate(lines) if i >= i_cat and short(l)]
    for k, (i, l) in enumerate(marks):
        end = marks[k + 1][0] if k + 1 < len(marks) else len(lines)
        body += [f"### {l.replace(' ', '')}", "", "\n".join(lines[i + 1 : end]), ""]
    write(out, "huixi", "正文.md", "\n".join(body) + "\n")


# ---------- 慎疾刍言 ----------
def build_shenji(lines, out):
    short = lambda l: len(l.replace(" ", "")) <= 6 and not re.search(r"[，。：；？！]", l)
    i_yin = idx(lines, lambda l: l == "引")
    i_first = next(i for i in range(i_yin + 1, len(lines)) if short(lines[i]))
    i_ba = idx(lines, lambda l: l == "跋")
    body = ["## 引", "", "\n".join(lines[i_yin + 1 : i_first]), ""]
    marks = [(i, l) for i, l in enumerate(lines) if i_first <= i and (i_ba < 0 or i < i_ba) and short(l)]
    for k, (i, l) in enumerate(marks):
        end = marks[k + 1][0] if k + 1 < len(marks) else (i_ba if i_ba > 0 else len(lines))
        body += [f"### {l.replace(' ', '')}", "", "\n".join(lines[i + 1 : end]), ""]
    write(out, "shenji", "正文.md", "\n".join(body) + "\n")


def main():
    key, src, outdir = sys.argv[1:4]
    lines = load(src)
    out = pathlib.Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    {"yixue": build_yixue, "shanghan": build_shanghan, "huixi": build_huixi, "shenji": build_shenji}[key](lines, out)


if __name__ == "__main__":
    main()
