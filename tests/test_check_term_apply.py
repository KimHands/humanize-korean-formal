"""check_term_apply.py 회귀 테스트. 실행: python3 -m unittest discover tests"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skill" / "humanize-korean-formal" / "scripts"))

from check_term_apply import changed_spans, find_problems  # noqa: E402

FIXTURE = (ROOT / "tests" / "fixtures" / "report_excerpt" / "input.md").read_text(encoding="utf-8")
RECOMMENDED_TERMS = {
    "숫자로 뭉갠다": "값으로 평균화한다",
    "평균에 묻힌다": "평균에서 식별되지 않는다",
    "그런데 그 분포의 꼬리에": "그러나 그 분포의 상위 구간에",
    "우리 데이터": "보유 데이터",
    "얹지 않았다": "적용하지 않았다",
    "쓰면 된다": "활용할 수 있다",
    "위에서 끊는다": "상위 순위부터 적용한다",
}


def apply_terms(text: str) -> str:
    for current, proposed in RECOMMENDED_TERMS.items():
        text = text.replace(current, proposed)
    return text


class TermOnlyChangesPass(unittest.TestCase):
    def test_fixture_recommended_terms_pass(self):
        self.assertEqual(find_problems(FIXTURE, apply_terms(FIXTURE)), [])

    def test_noun_ending_in_yo_is_not_haeyo_style(self):
        self.assertEqual(find_problems("추가 자료 필요.", "추가 자료 필수."), [])

    def test_heading_noun_ending_in_da_is_not_an_ending(self):
        self.assertEqual(find_problems("## 바다\n본문이다.", "## 해양\n본문이다."), [])

    def test_heading_example_keeps_number_order(self):
        before = "(1) 분석 단위 — 노선 12개가 아니라 정류장 86곳"
        self.assertEqual(find_problems(before, "(1) 분석 단위 — 노선 12개 대신 정류장 86곳"), [])

    def test_changed_spans_show_line_breaks(self):
        self.assertEqual(changed_spans("우리 데이터가 있다.", "우리\n데이터가 있다."), ["(없음) → ⏎"])

    def test_changed_spans_list_every_edit(self):
        spans = changed_spans("우리 데이터가 있다.", "보유 데이터가 있다.")
        self.assertEqual(spans, ["우리 → 보유"])


class InvariantViolationsAreReported(unittest.TestCase):
    def assertReported(self, before, after, label):
        problems = find_problems(before, after)
        self.assertTrue(any(p.startswith(label) for p in problems), problems)

    def test_number_change(self):
        self.assertReported("정류장이 28곳 있다.", "정류장이 30곳 있다.", "숫자")

    def test_swapped_numbers(self):
        self.assertReported("서울 7곳, 부산 20곳이다.", "서울 20곳, 부산 7곳이다.", "숫자")

    def test_flipped_sign(self):
        self.assertReported("변화율은 -3.5%다.", "변화율은 +3.5%다.", "숫자")

    def test_comparison_operator(self):
        self.assertReported("p < 0.05다.", "p > 0.05다.", "수식 기호")

    def test_latin_token(self):
        self.assertReported("Gi* 에서 뺐다.", "핫스팟 분석에서 뺐다.", "영문·기호")

    def test_book_title_quote(self):
        self.assertReported("『효과 없음』이라 했다.", "『효과 있음』이라 했다.", "인용")

    def test_register_change_with_period(self):
        self.assertReported("차이를 뭉갠다.", "차이를 평균화합니다.", "문장 끝 문체")

    def test_register_change_without_period(self):
        self.assertReported("효과가 있다", "효과가 있습니다", "문장 끝 문체")

    def test_unrecognised_ending_moved_between_sentences(self):
        self.assertReported("첫 결과다. 다음 항목.", "첫 결과. 다음 항목이다.", "문장 끝 문체")

    def test_register_swapped_between_sentences(self):
        self.assertReported("첫 결과다. 다음 결과입니다.", "첫 결과입니다. 다음 결과다.", "문장 끝 문체")


if __name__ == "__main__":
    unittest.main()
