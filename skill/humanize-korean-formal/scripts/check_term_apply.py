"""공식 용어 적용 전후 불변 항목 검사 (humanize-korean-formal Phase 3).

용어만 바꿔야 하므로 다음이 전후로 같아야 한다(모두 등장 순서까지 비교):
  - 숫자(부호 포함: 7, -3.5%, 1,200 …)
  - 비교·수식 기호(<, >, ≤, ≥, =, ≠, ±)
  - 영문·기호 토큰(Gi*, GIS, R² …) — 기법명·약어 근사
  - 인용 부호 안 내용("", '', 「」, 『』, 《》, 〈〉)
  - 문장별 끝 문체(해라체 / 합쇼체 / 해요체 / 기타) — 제목(#)·표(|) 줄은 문장이 아니라서 제외

검사하지 못하는 것: 한글 고유명사·주장의 뜻 변화, 숫자가 가리키는 대상의 변화.
그래서 바뀐 구간(줄바꿈 포함)을 모두 출력한다 — 사용자가 고른 번호와 하나씩 대조할 것.

사용:
  python3 check_term_apply.py --before 원문.md --after 적용본.md
exit 0 = 불변 / 1 = 차이 있음(목록 출력) / 3 = 입력 오류
"""
from __future__ import annotations

import argparse
import difflib
import re
import sys
from pathlib import Path

NUMBER_RE = re.compile(r"[-+−]?\d[\d,]*(?:\.\d+)?%?")
MATH_RE = re.compile(r"[<>≤≥=≠±]")
LATIN_RE = re.compile(r"[A-Za-z][A-Za-z0-9*²³_\-]*")
QUOTE_RE = re.compile(r"[\"“]([^\"”]+)[\"”]|['‘]([^'’]+)['’]|「([^」]+)」|『([^』]+)』|《([^》]+)》|〈([^〉]+)〉")
SENTENCE_END_RE = re.compile(r"[^.?!\n]+[.?!]?")
NON_SENTENCE_LINE_RE = re.compile(r"^\s*[#|]")
TOKEN_RE = re.compile(r"\n|[^\s]+")
ENDING_RULES = (
    ("합쇼체", re.compile(r"(?:니다|니까)$")),
    ("해요체", re.compile(r"(?:[아어여해워와봐줘]요|에요|예요|죠|지요|네요|군요|세요|래요|대요|가요|나요|까요|게요)$")),
    ("해라체", re.compile(r"다$")),
)


def extract_quotes(text: str) -> list[str]:
    return [next(group for group in match if group) for match in QUOTE_RE.findall(text)]


def classify_ending(sentence: str) -> str:
    core = sentence.strip().rstrip(".?!\"”’』」》〉)").strip()
    for name, rule in ENDING_RULES:
        if rule.search(core):
            return name
    return "기타"


def body_text(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not NON_SENTENCE_LINE_RE.match(line))


def sentence_endings(text: str) -> list[str]:
    chunks = (chunk for chunk in SENTENCE_END_RE.findall(body_text(text)) if chunk.strip())
    return [classify_ending(chunk) for chunk in chunks]


def diff_sequence(label: str, before: list[str], after: list[str]) -> list[str]:
    if before == after:
        return []
    matcher = difflib.SequenceMatcher(a=before, b=after, autojunk=False)
    problems = []
    for tag, b1, b2, a1, a2 in matcher.get_opcodes():
        if tag != "equal":
            problems.append(f"{label}: {before[b1:b2] or '없음'} → {after[a1:a2] or '없음'}")
    return problems or [f"{label}: 순서가 바뀜"]


def find_problems(before: str, after: str) -> list[str]:
    problems = diff_sequence("숫자", NUMBER_RE.findall(before), NUMBER_RE.findall(after))
    problems += diff_sequence("수식 기호", MATH_RE.findall(before), MATH_RE.findall(after))
    problems += diff_sequence("영문·기호", LATIN_RE.findall(before), LATIN_RE.findall(after))
    problems += diff_sequence("인용", extract_quotes(before), extract_quotes(after))
    problems += diff_sequence("문장 끝 문체", sentence_endings(before), sentence_endings(after))
    return problems


def show_tokens(tokens: list[str]) -> str:
    return " ".join("⏎" if token == "\n" else token for token in tokens) or "(없음)"


def changed_spans(before: str, after: str) -> list[str]:
    old_tokens, new_tokens = TOKEN_RE.findall(before), TOKEN_RE.findall(after)
    matcher = difflib.SequenceMatcher(a=old_tokens, b=new_tokens, autojunk=False)
    return [
        f"{show_tokens(old_tokens[b1:b2])} → {show_tokens(new_tokens[a1:a2])}"
        for tag, b1, b2, a1, a2 in matcher.get_opcodes()
        if tag != "equal"
    ]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def report(problems: list[str], spans: list[str]) -> int:
    print(f"바뀐 구간 {len(spans)}개 — 고른 번호와 하나씩 대조할 것:")
    for span in spans:
        print(f"  · {span}")
    if not problems:
        print("용어 적용 검사: OK — 숫자·수식 기호·영문 토큰·인용·문장 끝 문체 불변")
        return 0
    print("용어 적용 검사: 차이 있음 — 원문대로 되돌릴 것")
    for problem in problems:
        print(f"  - {problem}")
    return 1


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--before", required=True, type=Path)
    parser.add_argument("--after", required=True, type=Path)
    args = parser.parse_args()
    try:
        before, after = read_text(args.before), read_text(args.after)
    except (OSError, UnicodeDecodeError) as error:
        print(f"입력 오류: {error}", file=sys.stderr)
        return 3
    return report(find_problems(before, after), changed_spans(before, after))


if __name__ == "__main__":
    sys.exit(main())
