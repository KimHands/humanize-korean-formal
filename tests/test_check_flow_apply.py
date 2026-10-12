"""check_term_apply.py --mode flow 회귀 테스트. 실행: python3 -m unittest discover tests"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skill" / "humanize-korean-formal" / "scripts"))

from check_term_apply import find_flow_problems  # noqa: E402

FIXTURE = (ROOT / "tests" / "fixtures" / "flow_excerpt" / "input.md").read_text(encoding="utf-8")
GOOD_FLOW = """## (4) 분석 결과

3월 평일 오전을 대상으로 정류장 86곳의 대기 시간을 측정했다. 오전 혼잡은 A 노선에 몰렸고 B 노선은 좌석이 남았다. 배차 간격은 평균 15분이다. 평균 대기 시간은 12분이었다.

대기 시간이 20분을 넘는 정류장 7곳이 모두 A 노선에 있었고 이 7곳의 이용자는 하루 1,200명이다. 따라서 증차가 필요하다.

## (5) 활용 방안

학생지원팀은 학기 초에 이 목록을 갱신하고 시설팀은 정류장 위치를 점검한다. 운영 예산은 상위 정류장부터 배정하며 결과는 학기마다 공개한다.
"""


class FlowChangesPass(unittest.TestCase):
    def test_linking_and_reordering_within_paragraphs_pass(self):
        self.assertEqual(find_flow_problems(FIXTURE, GOOD_FLOW), [])

    def test_removing_crowded_connectives_passes(self):
        self.assertEqual(find_flow_problems("또한 A다. 또한 B다. 또한 C다.", "A이고 B이며 C다."), [])


class FlowViolationsAreReported(unittest.TestCase):
    def assertReported(self, after, label):
        problems = find_flow_problems(FIXTURE, after)
        self.assertTrue(any(label in p for p in problems), problems)

    def test_sentence_moved_across_paragraphs(self):
        moved = GOOD_FLOW.replace(" 평균 대기 시간은 12분이었다.", "").replace(
            "따라서 증차가 필요하다.", "따라서 증차가 필요하다. 평균 대기 시간은 12분이었다.")
        self.assertReported(moved, "숫자")

    def test_paragraphs_merged(self):
        self.assertReported(GOOD_FLOW.replace("12분이었다.\n\n대기", "12분이었다. 대기"), "문단 수")

    def test_heading_changed(self):
        self.assertReported(GOOD_FLOW.replace("## (5) 활용 방안", "## (5) 활용"), "소제목")

    def test_new_register_introduced(self):
        self.assertReported(GOOD_FLOW.replace("증차가 필요하다.", "증차가 필요합니다."), "원문에 없던 문장 끝 형태")

    def test_connectives_crowded_in(self):
        crowded = GOOD_FLOW.replace("평균 대기 시간은", "따라서 평균 대기 시간은").replace(
            "배차 간격은", "또한 배차 간격은").replace("오전 혼잡은", "그리고 오전 혼잡은")
        self.assertReported(crowded, "문두 접속사")

    def test_igneun_reference_added(self):
        self.assertReported(GOOD_FLOW.replace("따라서 증차가", "이는 증차가"), "이는")


class FlowEdgeCases(unittest.TestCase):
    def assertReported(self, before, after, label):
        problems = find_flow_problems(before, after)
        self.assertTrue(any(label in p for p in problems), problems)

    def test_sentence_without_numbers_moved_across_paragraphs(self):
        self.assertReported("조사를 실시했다. 결과를 공개했다.\n\n예산을 검토했다.",
                            "조사를 실시했다.\n\n결과를 공개했다. 예산을 검토했다.", "문단을 넘은 이동")

    def test_connectives_with_commas_are_counted(self):
        self.assertReported("조사했다. 검토했다. 공개했다.",
                            "또한, 조사했다. 따라서, 검토했다. 그러나, 공개했다.", "문두 접속사")

    def test_igneun_with_comma_is_counted(self):
        self.assertReported("조사를 했다.", "이는, 조사를 했다는 뜻이다.", "이는")

    def test_new_noun_ending_is_reported(self):
        self.assertReported("조사했다.", "조사했음.", "원문에 없던 문장 끝 형태")

    def test_injected_comma_after_linking_ending(self):
        self.assertReported("목록을 갱신한다. 위치를 점검한다.", "목록을 갱신하고, 위치를 점검한다.", "쉼표")

    def test_short_sentence_moved_across_paragraphs(self):
        self.assertReported("점검했다. 공개했다.\n\n검토했다.", "점검했다.\n\n공개했다. 검토했다.", "문단을 넘은 이동")

    def test_merged_and_moved_across_paragraphs(self):
        self.assertReported("조사를 실시했다. 결과를 공개했다.\n\n예산을 검토했다.",
                            "조사를 실시했다.\n\n결과를 공개하고 예산을 검토했다.", "문단을 넘은 이동")

    def test_comma_added_to_existing_linking_ending(self):
        self.assertReported("시설을 점검하고 결과를 공개했다.", "시설을 점검하고, 결과를 공개했다.", "쉼표")

    def test_too_many_linking_endings_in_new_sentence(self):
        self.assertReported("조사하고 검토했다. 기록했다. 공개했다.", "조사하고 검토하고 기록하고 공개했다.", "연결어미가")

    def test_protected_term_changed(self):
        problems = find_flow_problems("보유 데이터는 충분하다.", "보유 자료는 충분하다.", ["보유 데이터"])
        self.assertTrue(any("확정 용어" in p for p in problems), problems)

    def test_dedup_merge_of_repeated_subject_passes(self):
        self.assertEqual(find_flow_problems(
            "학생지원팀은 시설을 점검했다. 학생지원팀은 결과를 기록했다. 학생지원팀은 결과를 공개했다.",
            "학생지원팀은 시설을 점검하고 결과를 기록하고 공개했다."), [])

    def test_merge_with_identical_sentence_elsewhere_passes(self):
        self.assertEqual(find_flow_problems("결과를 공개했다. 조사를 실시했다.\n\n결과를 공개했다.",
                                            "결과를 공개하고 조사를 실시했다.\n\n결과를 공개했다."), [])

    def test_reordered_enumeration_noun_comma_passes(self):
        self.assertEqual(find_flow_problems("창고와 사무실, 회의실을 점검했다.", "사무실과 창고, 회의실을 점검했다."), [])

    def test_dropping_connective_from_existing_long_sentence_passes(self):
        long_sentence = ("정류장별 평균 대기 시간을 평일 오전과 오후 시간대에 걸쳐 모두 측정하여 노선별 시간대별 차이를 "
                         "상세하게 분석한 결과를 관련 자료와 함께 학생지원팀과 시설팀에 각각 전달했다.")
        self.assertEqual(find_flow_problems("또한 " + long_sentence, long_sentence), [])

    def test_existing_enumeration_comma_is_kept(self):
        self.assertEqual(find_flow_problems("창고, 사무실을 점검했다. 결과를 공개했다.",
                                            "창고, 사무실을 점검하고 결과를 공개했다."), [])

    def test_overlong_merged_sentence(self):
        before = ("정류장별 평균 대기 시간을 평일 오전과 오후 시간대에 걸쳐 모두 측정했다. "
                  "측정 결과는 노선별·시간대별로 나누어 표 형식으로 정리했다. "
                  "정리한 표는 학생지원팀과 시설팀에 각각 전달했다.")
        after = ("정류장별 평균 대기 시간을 평일 오전과 오후 시간대에 걸쳐 모두 측정하고 "
                 "측정 결과는 노선별·시간대별로 나누어 표 형식으로 정리했으며 "
                 "정리한 표는 학생지원팀과 시설팀에 각각 전달했다.")
        self.assertReported(before, after, "70자")


if __name__ == "__main__":
    unittest.main()
