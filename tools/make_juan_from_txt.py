#!/usr/bin/env python3
"""把「医藏」体电子校点文本整理为仓库 Markdown 格式（按卷输出）。

用法:
    python3 tools/make_juan_from_txt.py <输入txt> <书名> <卷名> <输出md>

说明:
    输入文本是网上流传的「医藏」体校点本，属**现代转录**，不是底本。
    它只作录入底稿；正式文本必须与影印底本逐段核对。
"""

import re
import sys
import pathlib

NUM = r"[一二三四五六七八九十百]+难"


def clean(line: str) -> str:
    return line.replace("\u3000", "").replace("\ufeff", "").strip()


def load_lines(path: str):
    text = pathlib.Path(path).read_text(encoding="utf-8", errors="ignore")
    return [l for l in (clean(x) for x in text.splitlines()) if l]


def section(lines, start_mark, end_mark):
    try:
        i = lines.index(start_mark)
    except ValueError:
        raise SystemExit(f"未找到卷标记: {start_mark}")
    j = lines.index(end_mark) if end_mark else len(lines)
    return lines[i + 1 : j]


def to_md(body_lines, book: str, juan: str, header: str) -> str:
    body = "\n".join(body_lines)
    out = [header, "", f"# {book}", "", f"## {juan}", ""]
    marks = list(re.finditer(r"(" + NUM + r")(曰[：:])", body))
    if not marks:
        out.append(body)
        return "\n".join(out)

    pre = body[: marks[0].start()].strip()
    if pre:
        out += [pre, ""]

    for k, m in enumerate(marks):
        end = marks[k + 1].start() if k + 1 < len(marks) else len(body)
        chunk = body[m.start() : end].strip()
        out += [f"### {m.group(1)}", "", chunk, ""]
    return "\n".join(out).rstrip() + "\n"


def main():
    src, book, juan, dst = sys.argv[1:5]
    lines = load_lines(src)

    marks = [l for l in lines if l in ("卷上", "卷下")] or ["卷上"]
    target = "卷下" if juan == "卷下" else "卷上"

    if target == "卷上":
        end_mark = "卷下" if "卷下" in lines else None
        body = section(lines, "卷上", end_mark)
    else:
        body = section(lines, "卷下", None)

    header = (
        f"<!-- 文件路径：{book}/{pathlib.Path(dst).name} -->\n"
        "<!-- 底本：徐氏醫書系统影印本（Commons YNUTCM-294300191）；半松斋原刻单行本未见公开扫描，待补 -->\n"
        "<!-- 录入底稿：网络「医藏」电子校点本，属现代转录；本卷尚未逐段比对影印件，标记为待核 -->"
    )
    md = to_md(body, book, target, header)
    pathlib.Path(dst).write_text(md, encoding="utf-8")
    print(f"wrote {dst}: {len(md)} chars")


if __name__ == "__main__":
    main()
