# humanize-korean-formal — 에이전트 작업 규칙

[humanize-korean](https://github.com/epoko77-ai/im-not-ai) v2.3.2(MIT)를 복사해 **공식 용어 검토 단계(Phase 3)**를 더한 Claude Code 스킬 저장소.
산출물은 스킬 폴더 하나: `skill/humanize-korean-formal/` (설치 위치 `~/.claude/skills/humanize-korean-formal/`).

## 원본과의 관계
- 원본에서 가져온 파일(`references/` 기존 파일, `agents/`, `scripts/` 런타임 9종)은 **원본과 같게 유지**한다.
  고쳐야 하면 최소 범위로 고치고 `skill/humanize-korean-formal/README.md` 「원본과 달라진 점」에 적는다.
- `LICENSE`(원본 MIT 고지)는 수정·삭제하지 않는다. 스킬 폴더를 어디로 복사하든 함께 간다.

## 공식 용어 검토 규칙 (Phase 3 를 고칠 때 지킬 것)
- 입력 글에서 비유·구어 표현을 찾아 **후보 표**를 먼저 낸다: 위치 · 현재 표현 · 제안(공식 용어) · 분류
- 분류: A 비유(권장) / B 1인칭·구어(권장) / C 소제목(선택) / D 제목(선택) / E 유지(학술·기술 용어)
- **사용자가 고른 것만 적용한다.** 표를 내기 전에 원문을 고치지 않는다. "바로 완성본"을 요청받아도 같다.
- 숫자·주장·고유명사·인용은 바꾸지 않는다. 용어만 바꾼다(`scripts/check_term_apply.py` 로 검사).
- 학술·기술 용어(예: 공간 해상도, 강건성, 고립 지점)는 비유처럼 보여도 E 유지로 분류한다. 단 정의대로 쓰지 않았으면 A 로 올리고 "E 가능"을 적는다.
- 문체(해라체 등)와 문장 끝은 원문을 따른다.
- 용어 검토는 항상 윤문 **뒤**에 한다.

## 검증
- 단위 테스트: `python3 -m unittest discover tests`
- 행동 테스트: `tests/fixtures/report_excerpt/input.md` 를 스킬에 넣고 `expected.md` 의 분류 정답·멈춤 조건과 대조한다.
  SKILL.md 나 `references/formal-terms.md` 를 고치면 다시 돌린다(스킬 문구 변경은 동작 변경이다).
- 예문·픽스처에는 실제 제출물·개인 문서를 넣지 않는다. 가상 예문만 쓴다.

## 규칙
- 푸시·태그·릴리스는 저장소 관리자 확인 후에만 한다.
