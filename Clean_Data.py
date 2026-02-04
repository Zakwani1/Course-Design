import re
from pathlib import Path


def detect_encoding(path: Path):
    try:
        with path.open("r", encoding="utf-8") as f:
            f.read()
        return "utf-8"
    except UnicodeDecodeError:
        return "gbk"


def remove_parentheses_and_contents(s: str) -> str:
    # Iteratively remove innermost bracketed segments for many bracket types.
    patterns = [
        r"\([^()]*\)",
        r"（[^（）]*）",
        r"\[[^\[\]]*\]",
        r"\{[^{}]*\}",
        r"<[^<>]*>",
        r"【[^】]*】",
        r"《[^》]*》",
        r"〖[^〗]*〗",
        r"〔[^〕]*〕",
    ]
    prev = None
    while prev != s:
        prev = s
        for p in patterns:
            s = re.sub(p, "", s)

    # remove any leftover standalone bracket characters
    leftover = r"[\(\)\[\]\{\}<>（）【】《》〖〗〔〕]+"
    s = re.sub(leftover, "", s)
    return s


def remove_quotes(s: str) -> str:
    # remove ASCII and common Chinese quote characters
    quotes = '"\'“”‘’『』「」‹›«»'
    return s.translate({ord(c): None for c in quotes})


def clean_file(input_path: Path, output_path: Path):
    enc = detect_encoding(input_path)
    total = 0
    skipped_hyphen = 0
    written = 0
    with input_path.open("r", encoding=enc, errors="ignore") as inf, output_path.open("w", encoding="utf-8", newline="") as outf:
        for raw_line in inf:
            total += 1
            if "-" in raw_line:
                skipped_hyphen += 1
                continue
            line = raw_line.rstrip("\n\r")
            line = remove_parentheses_and_contents(line)
            line = remove_quotes(line)
            # remove phrases like 学制4年, 学制 4 年, 学制12年 etc. (X is digits)
            line = re.sub(r"学制\s*\d+\s*年", "", line)
            line = line.strip()
            if line == "":
                continue
            outf.write(line + "\n")
            written += 1

    print(f"Input: {input_path}\nOutput: {output_path}")
    print(f"Total lines read: {total}")
    print(f"Skipped lines containing '-': {skipped_hyphen}")
    print(f"Lines written: {written}")


if __name__ == "__main__":
    base = Path(__file__).parent
    inp = base / "招生数据.csv"
    out = base / "招生数据_clean.csv"
    if not inp.exists():
        print(f"源文件未找到: {inp}")
    else:
        clean_file(inp, out)
