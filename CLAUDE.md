# CLAUDE.md

CAMCA — 천식 흡입제 사용법 자동 평가 시스템. 연구 문서(Research Proposal·IRB·method/)와
분석 엔진(`camca-py`)·웹 플랫폼(`camca-web`)이 한 저장소에 있음.

- 분석 엔진: `camca-py/` (segmentation·telemetry·pipeline, pytest)
- 웹 플랫폼: `camca-web/` (FastAPI 모놀리스, pytest)
- 설계 스펙·계획: `docs/superpowers/`
- 알고리즘 스펙: `method/10_video_analysis_algorithm.md` (Research Proposal v1.3의 컴패니언)

## Skill routing

When the user's request matches an available skill, invoke it via the Skill tool. When in doubt, invoke the skill.

Key routing rules:
- Product ideas/brainstorming → invoke /office-hours
- Strategy/scope → invoke /plan-ceo-review
- Architecture → invoke /plan-eng-review
- Design system/plan review → invoke /design-consultation or /plan-design-review
- Full review pipeline → invoke /autoplan
- Bugs/errors → invoke /investigate
- QA/testing site behavior → invoke /qa or /qa-only
- Code review/diff check → invoke /review
- Visual polish → invoke /design-review
- Ship/deploy/PR → invoke /ship or /land-and-deploy
- Save progress → invoke /context-save
- Resume context → invoke /context-restore
- Author a backlog-ready spec/issue → invoke /spec
