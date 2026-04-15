# Wwise Bus Routing Auditor
<img width="1490" height="1003" alt="image" src="https://github.com/user-attachments/assets/db1e4cc7-0c6d-4c69-84d0-b6ef66e57f2b" />

Wwise Authoring Tool의 **Tools 메뉴**에서 실행하는 버스 라우팅 검수 툴입니다.  
프로젝트 전체 Sound 오브젝트를 스캔하여 **에셋 이름** 또는 **Work Unit / 계층 경로** 기준으로  
버스 라우팅 위반을 탐지하고, 선택한 항목을 일괄 재라우팅합니다.
지원 언어 : EN/KOR

설치 전 실행중인 Wwise와 Wwise Launcher를 종료하고 설치하십시오.

> **Wwise 2023 · 2024 · 2025 호환**  
> Wwise 종료 시 툴도 자동으로 함께 종료됩니다.

---

## 목차

- [사전 요구사항](#사전-요구사항)
- [설치 방법](#설치-방법)
- [사용 방법](#사용-방법)
- [스캔 모드](#스캔-모드)
- [다중 키워드 OR 검색](#다중-키워드-or-검색)
- [검색 및 필터](#검색-및-필터)
- [신호 흐름 탭](#신호-흐름-탭)
- [히트맵 탭](#히트맵-탭)
- [결과 색상 기준](#결과-색상-기준)
- [버스 해석 알고리즘](#버스-해석-알고리즘)
- [트러블슈팅](#트러블슈팅)
- [기술 스택](#기술-스택)
- [파일 구성](#파일-구성)

---

## 사전 요구사항

- **Python 3.10 이상** — [python.org](https://www.python.org)
- **Wwise WAAPI 활성화**  
  `Project > User Preferences > Enable Wwise Authoring API (WAAPI)`  
  (기본 포트: **8080**)

---

## 설치 방법

### 1단계 — 저장소 클론 또는 ZIP 다운로드

```bash
git clone https://github.com/samter96/Wwise-Bus-Routing-Auditor.git
```

또는 페이지 상단 **Code → Download ZIP** 으로 다운로드 후 원하는 위치에 압축 해제.

### 2단계 — 가상환경 및 패키지 설치

[`install.bat`](install.bat) 을 실행합니다.

```
install.bat
```

`.venv` 폴더가 생성되고 `waapi-client` 가 자동 설치됩니다.

### 3단계 — Wwise Tools 메뉴 등록

[`install_addon.bat`](install_addon.bat) 을 실행합니다.

```
install_addon.bat
```

아래 경로에 Add-on 파일이 자동 생성됩니다.

```
%APPDATA%\Audiokinetic\Wwise\Add-ons\Commands\BusRoutingAuditor.json
```

### 4단계 — Wwise에서 확인

Wwise가 열려 있다면 **메뉴 → Tools → Reload Command Add-ons**  
또는 Wwise를 재시작하면 **Tools → Bus Routing Auditor** 가 나타납니다.

---

## 사용 방법

1. Wwise 메뉴 → `Tools > Bus Routing Auditor` 클릭

<img width="702" height="53" alt="image" src="https://github.com/user-attachments/assets/2eb937cb-63fc-4a12-9a58-ebc8ea6c87db" />

2. 상단에 **"연결됨"** 상태가 표시되면 준비 완료

<img width="752" height="39" alt="image" src="https://github.com/user-attachments/assets/502166f2-222c-4f7f-8986-3e6951590e3c" />

3. **스캔 1 / 스캔 2** 탭에서 룰 설정 후 **▶ 스캔 실행**

<img width="1602" height="917" alt="image" src="https://github.com/user-attachments/assets/63fa171d-6aab-4846-8ac8-0d79346ec6f8" />

4. 결과 목록에서 위반 항목 확인
   - 항목 **더블클릭** → Wwise Project Explorer에서 해당 오브젝트 자동 선택
   - 항목 선택(다중 가능) 후 **⟲ 일괄 재라우팅** 으로 버스 수정
   
<img width="1604" height="915" alt="image" src="https://github.com/user-attachments/assets/71625754-6912-4ce7-8cb3-18efef31d2d8" />

5. **↓ CSV 내보내기** 로 결과를 파일로 저장
6. **신호 흐름** 탭에서 버스별 위반 에셋과 라우팅 경로를 시각적으로 확인

<img width="1603" height="906" alt="image" src="https://github.com/user-attachments/assets/f3be1855-5cc7-4acb-9d77-528145b47146" />

7. **히트맵** 탭에서 버스별 위반율을 한눈에 파악

<img width="1612" height="856" alt="image" src="https://github.com/user-attachments/assets/1a4f430d-ba0f-463e-9471-d366900763e5" />

> Wwise를 종료하면 툴도 자동으로 함께 닫힙니다.

---

## 스캔 모드

### 스캔 1 — 에셋 이름 기준

Sound 오브젝트의 **이름**을 단어 토큰 단위로 검사합니다.

| 상황 | 판정 |
|------|------|
| 이름에 `UI` 포함 + 버스 이름에 `UI` 있음 | ✅ 정상 |
| 이름에 `UI` 포함 + 버스 이름에 `UI` 없음 | ❌ 위반 |
| 이름에 `UI` 포함 + 버스 미설정 (상속됨) | ⚠ 위반 (옵션) |

**★단어 토큰이란?**  
`_` / Space / `-` / `.` 등으로 구분된 단어 단위입니다.  
`UI` → `UI_Click` ✓ · `NPC_UI` ✓ · `BUILD` ✗ · `QUIT` ✗

### 스캔 2 — Work Unit / 경로 기준 (추천)

Sound의 **소속 경로**를 검사합니다.  
검색 대상: Work Unit 이름 + Work Unit 전체 경로 (Sound 이름 제외)

| 상황 | 판정 |
|------|------|
| 경로에 `UI` 포함 + 버스 이름에 `UI` 있음 | ✅ 정상 |
| 경로에 `UI` 포함 + 버스 이름에 `UI` 없음 | ❌ 위반 |

> **⚠ 키워드는 단어 경계 기준으로 매칭됩니다.**  
> `VIDEO` 키워드는 `VIDEO_Main`, `VIDEO_Dialogue` 모두 매칭합니다.  
> 특정 Work Unit만 검색하려면 이름 전체를 키워드로 설정하세요. (예: `VIDEO_Main`)

---

## 다중 키워드 OR 검색

각 룰 행에서 `+` 버튼으로 OR 조건을 추가할 수 있습니다.

| 버튼 색상 | 대상 |
|-----------|------|
| 🟢 초록 `+` | 소스 키워드 (에셋 이름 / WU 경로) OR 추가 |
| 🔵 파랑 `+` | 버스 이름 키워드 OR 추가 |

**예시** — AMB 경로 에셋이 `AMB` 또는 `Ambisonics` 버스에 라우팅된 경우 모두 허용:

```
WU 경로 키워드: AMB   →   버스 키워드: AMB
                              or Ambisonics
```

---

## 검색 및 필터

### 결과 검색창

| 입력 예 | 동작 |
|---------|------|
| `UI` | 이름/경로에 `UI` 토큰 포함 항목만 표시 |
| `UI Metal` | `UI` **and** `Metal` 모두 포함 항목만 표시 (AND 검색) |

검색 필드를 콤보박스로 선택할 수 있습니다 (전체 / 에셋 이름 / Work Unit / 현재 버스 / 기대 버스 키워드).

### 스캔 2 전용 필터

| 체크박스 | 표시 대상 |
|---------|-----------|
| **↑ 상속됨** (노랑) | 버스가 부모로부터 상속된 항목 |
| **◆ 오버라이드됨** (빨강) | 버스가 명시적으로 설정된 항목 |

---

## 신호 흐름 탭

스캔 실행 후 **신호 흐름** 탭에서 버스별 위반 현황을 시각적으로 확인할 수 있습니다.

- **좌측 버스 트리**: 실제 Wwise 버스 계층과 동기화. 위반 항목이 있는 버스는 자동으로 펼쳐집니다.
- **우측 위반 목록**: 출처(에셋이름 / WU), 현재 버스, 기대 키워드, 경로 표시
  - 항목 **더블클릭** → Wwise에서 해당 오브젝트 자동 선택
- **신호 흐름 캔버스**: Sound → 결정 지점 → 현재 버스 경로를 다이어그램으로 표시
- **출처 필터**: 에셋이름 스캔 위반 / WU 스캔 위반 각각 on/off

> 스캔 실행 후 Wwise 프로젝트 변경 시 자동 리빌드됩니다. 상태 바의 `⚡ 자동감지 N개` 로 활성 여부를 확인할 수 있습니다.

---

## 히트맵 탭

버스별 위반율을 컬러 격자로 표시합니다.

| 색상 | 위반율 |
|------|--------|
| 🟢 초록 | 0% |
| 🟡 노랑 | 1% – 14% |
| 🟠 주황 | 15% – 34% |
| 🔴 빨강 | 35% 이상 |

셀 클릭 시 **신호 흐름 탭**으로 이동하여 해당 버스의 위반 목록을 바로 확인할 수 있습니다.

---

## 결과 색상 기준

| 색상 | 의미 |
|------|------|
| 🔴 빨강 | 버스가 명시적으로 설정되어 있지만 규칙 위반 |
| 🟡 노랑 | 버스 미설정 (상속됨) — 규칙 적용 불가 상태 |
| 🟢 초록 | 스캔 완료 후 위반 없음 |

---

## 버스 해석 알고리즘

WAAPI의 `@OutputBus`는 로컬 저장값만 반환합니다.  
`@OverrideOutput=false`인 경우 스테일(잔류값)일 수 있으므로 3단계 우선순위로 유효 버스를 결정합니다.

| 단계 | 방법 | 설명 |
|------|------|------|
| Phase 1 | `@OverrideOutput=true` 조상 탐색 | 가장 가까운 오버라이드 조상 (캐시 사용) |
| Phase 2 | 스테일 비기본값 조상 탐색 | 루트에 가장 가까운 stale 조상 반환 (중간 컨테이너 잔류값 무시) |
| Phase 3 | Sound 자체 `@OutputBus` | Phase 1+2 결과가 Master Audio Bus일 때만 적용 (Silence 등 내부 생성 SFX 전용) |

---

## 트러블슈팅

| 증상 | 해결 방법 |
|------|-----------|
| "Wwise 연결 실패" | Wwise 실행 여부 확인 / `Enable WAAPI` 체크 / 포트 8080 방화벽 확인 |
| "waapi-client 미설치" | `install.bat` 재실행 |
| Tools 메뉴에 항목 없음 | `install_addon.bat` 재실행 후 Wwise 재시작 또는 `Tools > Reload Command Add-ons` |
| Wwise에서 보기 미동작 | Wwise 버전에 따라 자동으로 호환 커맨드를 탐색합니다. 그래도 안 되면 Project Explorer에서 수동 검색 |
| 툴이 자동으로 닫힘 | 정상 동작입니다. Wwise 종료 시 자동으로 함께 닫힙니다 |
| 스캔 결과가 예상과 다름 | 룰 저장 후 스캔했는지 확인하세요 (`⚠ 룰 변경 시 저장 후 스캔`) |
| 신호 흐름 탭이 비어 있음 | 스캔 실행 후 탭을 열어주세요. 자동 리빌드가 활성화되면 이후 변경 시 자동 갱신됩니다 |

---

## 기술 스택

| 역할 | 라이브러리 / 도구 |
|------|------------------|
| GUI | Python `tkinter` |
| Wwise 연동 | [`waapi-client`](https://pypi.org/project/waapi-client/) (WebSocket `ws://127.0.0.1:8080`) |
| 주요 WAAPI | `ak.wwise.core.object.get` · `ak.wwise.ui.commands.execute` · `ak.wwise.core.object.setReference` |

---

## 파일 구성

```
Wwise-Bus-Routing-Auditor\
  ├── bus_routing_auditor.py   ← 메인 소스 (tkinter GUI + WAAPI)
  ├── launch.bat               ← Wwise Add-on 진입점
  ├── install.bat              ← 가상환경 + 패키지 설치
  ├── install_addon.bat        ← Wwise Tools 메뉴 자동 등록
  ├── requirements.txt
  ├── README.md
  ├── DEVLOG.md
  ├── .gitignore
  └── .venv\                   ← 로컬 생성, git 미포함

%APPDATA%\Audiokinetic\Wwise\Add-ons\Commands\
  └── BusRoutingAuditor.json   ← install_addon.bat 이 자동 생성
```

`bus_routing_rules.json` (룰 저장 파일) 은 처음 저장 시 자동 생성됩니다 (git 미포함).

---

## 버전

**V.2.0.0** — 2026-04-15
