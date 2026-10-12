# humanize-korean-formal

한글 AI 티 제거 스킬 **humanize-korean v2.3.2**에 **공식 용어 검토 단계(Phase 3)**를 더한 사용자 스킬.

> **비공식 파생본입니다.** 원저작자(epoko77-ai)와 관계가 없으며, 원저작자가 제공하거나 검토한 변형이 아닙니다.
> 저장소: https://github.com/KimHands/humanize-korean-formal
보고서·공문서·공모전 제출물에서 비유·구어·1인칭 표현을 찾아 후보 표(위치·현재·제안·분류)를 먼저 내고, 사용자가 고른 항목만 공식 용어로 바꾼다.

## 출처와 라이선스

- 원본: im-not-ai 마켓플레이스 `humanize-korean` 플러그인 v2.3.2 (저작권자 epoko77-ai) — 기준 스냅샷 https://github.com/epoko77-ai/im-not-ai/tree/v2.3.2
- 라이선스: **MIT** — 원문은 이 폴더의 `LICENSE` (원본 그대로, 수정하지 않음)
- MIT 조건: 사용·복사·수정·병합·배포·재라이선스·판매 모두 허용. 단 **사본이나 상당 부분을 배포할 때는 저작권 고지와 허가 문구(`LICENSE`)를 함께 포함해야 한다.** 보증 없음.
- 이 폴더를 다른 곳에 복사·공유할 때 `LICENSE` 를 빼지 않는다.

## 원본에서 가져온 것

| 원본 경로 (플러그인 루트 기준) | 여기 | 수정 |
|---|---|---|
| `skills/humanize-korean/SKILL.md` | `SKILL.md` | 있음 — 아래 참조 |
| `skills/humanize-korean/references/*` | `references/*` | 없음 (파일 추가만) |
| `scripts/` 런타임 9종 | `scripts/` | references 경로 한 줄씩(4개 파일) |
| `agents/humanize-{monolith,diagnostician,finalizer}.md` | `agents/` | 없음 |
| `LICENSE` | `LICENSE` | 없음 |

가져오지 않은 것: 유지보수·개발용 에이전트 6종, 빌드·평가 스크립트, `tests/`, 설치 스크립트, 명령(`commands/`), Codex·Gemini 어댑터.

## 원본과 달라진 점

1. **Phase 3 공식 용어 검토 추가** (`SKILL.md` 「Phase 3」, `references/formal-terms.md`)
   - 분류: A 비유(권장) / B 1인칭·구어(권장) / C 소제목(선택) / D 제목(선택) / E 유지(학술·기술 용어)
   - 후보 표를 내고 멈춘다("용어 검토만" 모드는 첫 응답이 표뿐이고, "윤문 + 용어 검토" 모드는 윤문본 뒤에 표를 붙인다). 사용자가 고른 번호만 적용한다.
   - 숫자·수식 기호·영문 토큰·인용·문장별 끝 문체 불변은 `scripts/check_term_apply.py` 로 검사하고(추가 파일), 바뀐 구간을 모두 출력해 고른 번호와 대조한다. 한글 고유명사·주장의 뜻 변화는 스크립트가 판정하지 못한다.
2. **모드 결정** — "용어 검토만" / "윤문 + 용어 검토"(윤문을 먼저 하고 그 결과에 용어 검토를 한다).
3. **설치 구조** — 플러그인이 아니라 `~/.claude/skills/humanize-korean-formal/` 한 폴더에 설치된다.
   - `SKILL_ROOT` 를 `.claude-plugin/` 을 찾아 올라가는 방식에서 스킬 폴더 자체로 바꿨다.
   - 스크립트 4개(`prepare_monolith_input`·`verify_gates`·`restore_modality`·`verify_change_rate`)의 references 경로를 `../skills/humanize-korean/references` → `../references` 로 바꿨다.
   - 에이전트는 서브에이전트 타입으로 등록되지 않으므로 `general-purpose` 에이전트에게 `agents/*.md` 를 읽혀 실행한다.
4. **트리거** — 공식 용어·보고서체 요청에만 뜨도록 description 을 좁혔다. 일반 AI 티 제거는 원본 humanize-korean 이 맡는다.

## 설치

저장소 `skill/humanize-korean-formal/` 이 원본이고, `~/.claude/skills/humanize-korean-formal/` 에 **복사**해 설치한다. 저장소에서 고친 뒤에는 다시 복사해야 반영된다.

```bash
rsync -a --delete --exclude __pycache__ \
  <저장소 경로>/skill/humanize-korean-formal/ \
  ~/.claude/skills/humanize-korean-formal/
```

## 사용 예

- "이 보고서 비유·구어 표현 공식 용어로 바꿔 줘" → 용어 검토만: 후보 표 → 선택 → 적용
- "AI 티 빼고 보고서에 맞는 공식 용어로 정리해 줘" → 윤문 → 게이트 → 후보 표 → 선택 → 적용
- 표를 받은 뒤: "권장만" / "권장+소제목" / "전부" / "1, 3, 7번"
