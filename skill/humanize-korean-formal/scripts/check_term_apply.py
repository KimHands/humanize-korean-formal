"""용어·흐름 적용 전후 불변 항목 검사 (humanize-korean-formal Phase 3·4).

--mode term (Phase 3, 기본) — 용어만 바꾸므로 다음이 전후로 같아야 한다(모두 등장 순서까지 비교):
  - 숫자(부호 포함: 7, -3.5%, 1,200 …)
  - 비교·수식 기호(<, >, ≤, ≥, =, ≠, ±)
  - 영문·기호 토큰(Gi*, GIS, R² …) — 기법명·약어 근사
  - 인용 부호 안 내용("", '', 「」, 『』, 《》, 〈〉)
  - 문장별 끝 문체(해라체 / 합쇼체 / 해요체 / 기타) — 제목(#)·표(|) 줄은 문장이 아니라서 제외

--mode flow (Phase 4) — 문장을 묶고 같은 문단 안에서 순서를 바꿀 수 있으므로:
  - 소제목(#) 줄과 문단 수는 그대로
  - 다른 문단에 있던 낱말(2음절 어간)이 새로 나타나면 안 된다 — 문단을 넘은 이동(어미가 바뀌어도 잡는다)
  - 숫자·수식 기호·영문 토큰·인용은 **문단마다** 개수가 같아야 한다(문단 안 순서는 자유)
  - 원문에 없던 문장 끝 형태(예: 해라체 글에 합쇼체·"~음.")가 새로 나오면 안 된다
  - 문두 접속사를 늘려 한 문단 3개 이상이 되거나, "이는"으로 시작하는 문장이 늘면 안 된다(쉼표가 붙어도 센다)
  - 새로 생긴 낱말의 연결어미 뒤 쉼표(원본 C-11), 문단의 기존 최장 문장보다 길면서 공백 빼고 70자를 넘는 새 문장,
    연결어미 3개 이상 이어진 새 문장(기존보다 많을 때)
  - --protect 파일의 표현(Phase 3 에서 확정한 용어, 한 줄에 하나)은 개수가 그대로
  - 검사하지 못하는 것(흐름): 문체가 섞인 글에서 문장끼리 문체를 맞바꾼 것, 같은 문단 안에서 문장을 지운 것
    (바뀐 구간 목록으로 확인)

검사하지 못하는 것: 한글 고유명사·주장의 뜻 변화, 숫자가 가리키는 대상의 변화.
그래서 바뀐 구간(줄바꿈 포함)을 모두 출력한다 — 사용자가 고른 번호와 하나씩 대조할 것.

사용:
  python3 check_term_apply.py --before 원문.md --after 적용본.md [--mode term|flow] [--protect 용어목록.txt]
exit 0 = 불변 / 1 = 차이 있음(목록 출력) / 3 = 입력 오류
"""
from __future__ import annotations

import argparse
import difflib
import re
import sys
from collections import Counter
from pathlib import Path

NUMBER_RE = re.compile(r"[-+−]?\d[\d,]*(?:\.\d+)?%?")
MATH_RE = re.compile(r"[<>≤≥=≠±]")
LATIN_RE = re.compile(r"[A-Za-z][A-Za-z0-9*²³_\-]*")
QUOTE_RE = re.compile(r"[\"“]([^\"”]+)[\"”]|['‘]([^'’]+)['’]|「([^」]+)」|『([^』]+)』|《([^》]+)》|〈([^〉]+)〉")
SENTENCE_END_RE = re.compile(r"[^.?!\n]+[.?!]?")
NON_SENTENCE_LINE_RE = re.compile(r"^\s*[#|]")
TOKEN_RE = re.compile(r"\n|[^\s]+")
PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n")
OPENING_CONNECTIVE_RE = re.compile(
    r"(?:^|[.?!]\s+|\n)(또한|따라서|그리고|즉|나아가|아울러|게다가|더욱이|그러나|하지만|그런데|한편|반면|그래서|이에|이처럼)[\s,]"
)
OPENING_IGNEUN_RE = re.compile(r"(?:^|[.?!]\s+|\n)이는[\s,]")
LINKING_COMMA_TOKEN_RE = re.compile(r"(?:고|며|면서|는데|지만|어서|아서|해서|자|니까|므로),$")
LINKING_TOKEN_RE = re.compile(r"[가-힣]+(?:고|며|면서|는데|지만|어서|아서|해서|니까|므로),?$")
HANGUL_WORD_RE = re.compile(r"[가-힣]{2,}")
CONNECTIVE_WORDS = {"또한", "따라서", "그리고", "나아가", "아울러", "게다가", "더욱이", "그러나", "하지만",
                    "그런데", "한편", "반면", "그래서", "이에", "이처럼", "이는"}
FUNCTION_STEM_HEADS = set("하했한할해되된될됐있없이그저수것등및더또잘위때중")
CONNECTIVE_LIMIT = 3
LINKING_LIMIT = 3
NEW_SENTENCE_MAX_CHARS = 70
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


def headings(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.lstrip().startswith("#")]


def paragraphs(text: str) -> list[str]:
    return [block for block in PARAGRAPH_SPLIT_RE.split(text) if block.strip()]


def diff_multiset(label: str, before: list[str], after: list[str]) -> list[str]:
    if sorted(before) == sorted(after):
        return []
    return [f"{label}: {sorted(before)} → {sorted(after)}"]


def paragraph_invariants(index: int, before: str, after: str) -> list[str]:
    where = f"문단 {index}"
    problems = diff_multiset(f"{where} 숫자", NUMBER_RE.findall(before), NUMBER_RE.findall(after))
    problems += diff_multiset(f"{where} 수식 기호", MATH_RE.findall(before), MATH_RE.findall(after))
    problems += diff_multiset(f"{where} 영문·기호", LATIN_RE.findall(before), LATIN_RE.findall(after))
    problems += diff_multiset(f"{where} 인용", extract_quotes(before), extract_quotes(after))
    return problems


def sentences(text: str) -> list[str]:
    return [chunk.strip() for chunk in SENTENCE_END_RE.findall(body_text(text)) if chunk.strip()]


def content_stems(text: str) -> set[str]:
    words = (word for word in HANGUL_WORD_RE.findall(text) if word not in CONNECTIVE_WORDS)
    return {word[:2] for word in words if word[0] not in FUNCTION_STEM_HEADS}


def moved_words(before_blocks: list[str], after_blocks: list[str]) -> list[str]:
    stems_before = [content_stems(block) for block in before_blocks]
    problems = []
    for index, block in enumerate(after_blocks):
        for stem in sorted(content_stems(block) - stems_before[index]):
            sources = [j + 1 for j, stems in enumerate(stems_before) if j != index and stem in stems]
            if sources:
                problems.append(f"문단 {index + 1}에 문단 {sources}의 낱말 '{stem}…'이 새로 나타남 — 문단을 넘은 이동 의심")
    return problems


def linking_count(sentence: str) -> int:
    return sum(1 for token in sentence.split() if LINKING_TOKEN_RE.match(token))


def new_sentence_problems(index: int, before: str, after: str) -> list[str]:
    old_sentences = sentences(before)
    longest = max((len(s.replace(" ", "")) for s in old_sentences), default=0)
    most_linked = max((linking_count(s) for s in old_sentences), default=0)
    problems = []
    for sentence in set(sentences(after)) - set(old_sentences):
        length = len(sentence.replace(" ", ""))
        if length > NEW_SENTENCE_MAX_CHARS and length > longest:
            problems.append(f"문단 {index} 새 문장이 {NEW_SENTENCE_MAX_CHARS}자를 넘음: {sentence}")
        if linking_count(sentence) >= LINKING_LIMIT and linking_count(sentence) > most_linked:
            problems.append(f"문단 {index} 새 문장에 연결어미가 {LINKING_LIMIT}개 이상 이어짐: {sentence}")
    return problems


def used_as_noun(word: str, tokens: list[str]) -> bool:
    return any(len(token) > len(word) and token.startswith(word) and "가" <= token[len(word)] <= "힣" for token in tokens)


def injected_commas(index: int, before: str, after: str) -> list[str]:
    old_tokens = before.split()
    new_tokens = Counter(after.split()) - Counter(old_tokens)
    injected = [
        token for token in new_tokens.elements()
        if LINKING_COMMA_TOKEN_RE.search(token) and not used_as_noun(token.rstrip(","), old_tokens)
    ]
    return [f"문단 {index} 연결어미 뒤 쉼표가 새로 생김(원본 C-11): {injected}"] if injected else []


def protected_terms(before: str, after: str, terms: list[str]) -> list[str]:
    return [
        f"확정 용어 '{term}' {before.count(term)} → {after.count(term)}회"
        for term in terms
        if before.count(term) != after.count(term)
    ]


def connective_problems(index: int, before: str, after: str) -> list[str]:
    connectives_before = len(OPENING_CONNECTIVE_RE.findall(before))
    connectives_after = len(OPENING_CONNECTIVE_RE.findall(after))
    problems = []
    if connectives_after >= CONNECTIVE_LIMIT and connectives_after > connectives_before:
        problems.append(f"문단 {index} 문두 접속사 {connectives_before} → {connectives_after}개 (새로 늘려 한 문단 {CONNECTIVE_LIMIT}개 이상 금지)")
    if len(OPENING_IGNEUN_RE.findall(after)) > len(OPENING_IGNEUN_RE.findall(before)):
        problems.append(f"문단 {index} \"이는\"으로 시작하는 문장이 늘어남")
    return problems


def new_registers(before: str, after: str) -> list[str]:
    added = sorted(set(sentence_endings(after)) - set(sentence_endings(before)))
    return [f"원문에 없던 문장 끝 형태: {added}"] if added else []


def find_flow_problems(before: str, after: str, terms: list[str] | None = None) -> list[str]:
    problems = diff_sequence("소제목", headings(before), headings(after)) + protected_terms(before, after, terms or [])
    before_blocks, after_blocks = paragraphs(before), paragraphs(after)
    if len(before_blocks) != len(after_blocks):
        return problems + [f"문단 수: {len(before_blocks)} → {len(after_blocks)} (문단 경계를 넘으면 안 됨)"]
    problems += moved_words(before_blocks, after_blocks)
    for index, (old, new) in enumerate(zip(before_blocks, after_blocks), start=1):
        problems += paragraph_invariants(index, old, new) + new_sentence_problems(index, old, new)
        problems += injected_commas(index, old, new) + connective_problems(index, old, new)
    return problems + new_registers(before, after)


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


def read_terms(path: Path) -> list[str]:
    return [line.strip() for line in read_text(path).splitlines() if line.strip()]


def report(problems: list[str], spans: list[str]) -> int:
    print(f"바뀐 구간 {len(spans)}개 — 고른 번호와 하나씩 대조할 것:")
    for span in spans:
        print(f"  · {span}")
    if not problems:
        print("적용 검사: OK — 불변 항목 이상 없음")
        return 0
    print("적용 검사: 차이 있음 — 원문대로 되돌릴 것")
    for problem in problems:
        print(f"  - {problem}")
    return 1


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--before", required=True, type=Path)
    parser.add_argument("--after", required=True, type=Path)
    parser.add_argument("--mode", choices=("term", "flow"), default="term")
    parser.add_argument("--protect", type=Path, help="flow 모드: 개수를 유지할 확정 용어 목록(한 줄에 하나)")
    args = parser.parse_args()
    try:
        before, after = read_text(args.before), read_text(args.after)
    except (OSError, UnicodeDecodeError) as error:
        print(f"입력 오류: {error}", file=sys.stderr)
        return 3
    try:
        terms = read_terms(args.protect) if args.protect else []
    except (OSError, UnicodeDecodeError) as error:
        print(f"입력 오류: {error}", file=sys.stderr)
        return 3
    problems = find_flow_problems(before, after, terms) if args.mode == "flow" else find_problems(before, after)
    return report(problems, changed_spans(before, after))


if __name__ == "__main__":
    sys.exit(main())
