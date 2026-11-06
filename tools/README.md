# 제작·분석 도구

`work_ogg`에는 기존 작업의 Python 소스를 보존했습니다. `work_ogs`의 두 모듈은 해당 도구가 사용하는 공통 코덱·R5900 실행 검사기입니다. 별도 OGs 프로젝트의 게임이나 작업 결과는 포함하지 않습니다.

Python 3.11에서 작성했습니다. 외부 라이브러리는 `requirements.txt`에 정리했습니다.

## 범위와 입력

- `inspect_iso.py`, `inspect_resources.py`, `catalog.py`: ISO9660/LICE/마스터 테이블 분석.
- `build_selected_27.py`, `update_help_and_lineups.py`, `localize_*.py`: 편성 선정·제외와 한글 표시 수정.
- `plan_balance_25.py`, `apply_balance_25.py`: 추가 25편성의 능력치·무장 조정.
- `story_content_25.py`, `story_*.py`, `apply_story_25.py`: 작성한 대사, 합류 일정, 시나리오와 네이티브 훅.
- `campaign_*.py`, `apply_campaign_tuning.py`: 보상·적 강화·공통 무장 조정.
- `validate_*.py`, `story_vm.py`: 구조와 실제 게임 루틴 검사.
- `option_release/build_options.py`: 검증된 원본·최종 ISO와 변경 기록을 이용한 8옵션 데이터 생성.
- `option_release/validate_options.py`: 옵션을 합성하여 시나리오/보급 및 보상/적 강화 독립 동작 검사.

대부분은 `work_ogg/analysis`, ISO, 변경 저널, 이전 단계의 JSON 등 로컬 입력이 필요합니다. 입력에는 게임에서 추출한 데이터·RAM 덤프가 포함될 수 있어 이 저장소에 넣지 않았습니다. 따라서 이 소스만으로 게임 변경 과정을 처음부터 재현할 수는 없습니다. 배포용 패처는 릴리즈의 BIN과 루트 `build.ps1`만으로 빌드할 수 있습니다.

도구의 상대 경로는 당시 `work_ogg`/`work_ogs` 형제를 기준으로 합니다. 일부 실험용·예전 단계용 빌더는 과거 ISO 이름이나 PCSX2 설치 경로를 사용합니다. 사용 전 입력·출력 경로, 원본 해시, 적용 전 상태 가정을 확인하고 현재 작업 경로에 맞게 수정하세요. 일반 사용자는 이 도구를 실행할 필요 없이 릴리즈의 패처를 사용하면 됩니다.
