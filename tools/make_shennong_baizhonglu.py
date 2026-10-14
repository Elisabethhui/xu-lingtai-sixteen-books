#!/usr/bin/env python3
"""把「医藏」体文本整理为《神农本草经百种录》仓库格式（序／凡例／正文）。

用法:
    python3 tools/make_shennong_baizhonglu.py <输入txt> <输出目录>

输入文本属现代转录，仅作录入底稿；正式文本须与影印底本逐段核对。
"""

import pathlib
import sys

PIN = ("上品", "中品", "下品")
BOOK = "神农本草经百种录"


def clean(line: str) -> str:
    return line.replace("\u3000", "").replace("\ufeff", "").strip()


def load(path: str):
    text = pathlib.Path(path).read_text(encoding="utf-8", errors="ignore")
    return [l for l in (clean(x) for x in text.splitlines()) if l]


def header(filename: str) -> str:
    return (
        f"<!-- 文件路径：{BOOK}/{filename} -->\n"
        "<!-- 底本：徐氏醫書系统影印本（Commons，原件为清刻本）；半松斋原刻单行本未见公开扫描，待补 -->\n"
        "<!-- 录入底稿：网络「医藏」电子校点本，属现代转录；本篇尚未逐段比对影印件，标记为待核 -->"
    )


def write(outdir: pathlib.Path, filename: str, body: str):
    (outdir / filename).write_text(header(filename) + body, encoding="utf-8")
    print("wrote", filename, len(body), "chars")


def main():
    src, out = sys.argv[1:3]
    lines = load(src)
    outdir = pathlib.Path(out)
    outdir.mkdir(parents=True, exist_ok=True)

    # 定位各段
    i_seq = next((i for i, l in enumerate(lines) if l in ("序", "叙", "自序")), -1)
    i_fan = next((i for i, l in enumerate(lines) if l == "凡例"), -1)
    i_body = next((i for i, l in enumerate(lines) if l in PIN), -1)

    if i_seq < 0 or i_fan < 0 or i_body < 0:
        raise SystemExit(f"段落定位失败: 序={i_seq} 凡例={i_fan} 正文={i_body}")

    seq = lines[i_seq + 1 : i_fan]
    write(outdir, "自序.md", "\n\n" + f"# {BOOK}\n\n## 序\n\n" + "\n".join(seq) + "\n")

    fan = lines[i_fan + 1 : i_body]
    write(outdir, "凡例.md", "\n\n" + f"# {BOOK}\n\n## 凡例\n\n" + "\n".join(fan) + "\n")

    # 正文：每条 = 品级行 + 药名行 + 内容行
    out_lines = ["", "", f"# {BOOK}", "", "## 正文", ""]
    cur_pin = None
    i = i_body
    while i < len(lines):
        if lines[i] in PIN:
            pin = lines[i]
            name = lines[i + 1] if i + 1 < len(lines) else ""
            j = i + 2
            chunk = []
            while j < len(lines) and lines[j] not in PIN:
                chunk.append(lines[j])
                j += 1
            if pin != cur_pin:
                out_lines += [f"### {pin}", ""]
                cur_pin = pin
            out_lines += [f"#### {name}", "", "\n".join(chunk), ""]
            i = j
        else:
            i += 1

    write(outdir, "正文.md", "\n".join(out_lines).rstrip() + "\n")


if __name__ == "__main__":
    main()
