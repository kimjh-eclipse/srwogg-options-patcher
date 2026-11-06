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
- `option_release/build_options.py`: 검증된 원본·최종 ISO와 변경 기록을 이용한 7옵션 데이터 생성.
- `option_release/validate_options.py`: 옵션을 합성하여 시나리오/보급 및 보상/적 강화 독립 동작 검사.

대부분은 `work_ogg/analysis`, ISO, 변경 저널, 이전 단계의 JSON 등 로컬 입력이 필요합니다. 입력에는 게임에서 추출한 데이터·RAM 덤프가 포함될 수 있어 이 저장소에 넣지 않았습니다. 따라서 이 소스만으로 게임 변경 과정을 처음부터 재현할 수는 없습니다. 배포용 패처는 릴리즈의 BIN과 루트 `build.ps1`만으로 빌드할 수 있습니다.

도구의 상대 경로는 당시 `work_ogg`/`work_ogs` 형제를 기준으로 합니다. 일부 실험용·예전 단계용 빌더는 과거 ISO 이름이나 PCSX2 설치 경로를 사용합니다. 사용 전 입력·출력 경로, 원본 해시, 적용 전 상태 가정을 확인하고 현재 작업 경로에 맞게 수정하세요. 일반 사용자는 이 도구를 실행할 필요 없이 릴리즈의 패처를 사용하면 됩니다.

## 공식 베이스 검증

`work_ogg/upstream_base`에는 압축된 일본판 원본과 공식 xdelta를 ISO 복사본 없이 검증하는 도구가 있습니다. `decode_zip_vcdiff.py`는 xdelta의 무압축 recode를 읽어 RFC3284 기본 명령표로 디코딩하고 557개 구간 체크섬과 일본판 MD5를 확인합니다. `source_image.py`는 로컬 `official_base_delta.json`을 이용하는 읽기 전용 sparse overlay이며, `rebase_canonical.py`는 기존 확장 마스터의 문자열을 Strg/Sent ID로 이식합니다. 원본 ISO·공식 패치·게임 바이트를 담은 로컬 저널은 별도 입력입니다.

## 편성 보존 검사

`party_policy_25.py`는 독립 기체 그룹과 28화 기존 편성 복구 스크립트를 정의합니다. `apply_party_25.py`는 검증 결과·원본 해시를 확인하고 배타적으로 연 시험 ISO에 작은 변경 기록을 남겨 적용합니다. `validate_party_25.py`는 실제 저장 데이터 처리 루틴을 실행합니다. 수정 전의 린 그룹 참조는 메모리에서만 재구성하므로 적용 후에도 회귀 검사를 반복할 수 있습니다.

이 검사 역시 로컬의 ISO·합류 일정 JSON·실행 RAM·옵션 BIN·기존 변경 기록을 입력으로 사용합니다. 맵 유닛 조회를 부재 조건으로 대체하고 영구 저장 데이터의 VM 복원을 검사하므로 전편 플레이나 실제 메모리카드 검사를 대신하지 않습니다. 자세한 조건은 `docs/party-preservation-v20261106.3.md`에 있습니다.

## 본편 연결 대사

`story_consistency_policy.py`는 첫 구현인 `story_content_25.py`에 적용하는 추가 수정입니다. `story_consistency_logo.py`는 기존 이벤트 내부에서 장면을 이동하면서 분기 목적지와 대사 이력 위치를 보정합니다. `audit_story_consistency.py`는 현재 이미지의 장면 문맥을 읽고, `prepare_story_consistency.py`·`validate_story_consistency.py`·`apply_story_consistency.py`는 3단계 적용 전 이미지와 로컬 중간 자료를 사용하는 준비·검증·적용 도구입니다. 이미 적용된 이미지에 역사적 도구를 다시 실행하지 마세요. 현재 옵션 합성 결과의 선택·해제 검사는 `option_release/validate_options.py`가 담당합니다. [검증 범위와 대사](../docs/story-consistency-v20261106.4.md)를 참고하세요.
