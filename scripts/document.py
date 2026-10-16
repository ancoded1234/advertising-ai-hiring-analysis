from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];D=json.loads((R/'results/analysis.json').read_text(encoding='utf-8'));A=D['audit'];T=D['total'];P=lambda x:f'{x:.1%}'
role_table='\n'.join(f"|{r['role']}|{r['n']}|{r['genai']}|{P(r['rate'])}|{r['broad_ai']}|{P(r['broad_rate'])}|" for r in D['roles'])
company_table='\n'.join(f"|{r['company']}|{r['n']}|{r['genai']}|{r['broad_ai']}|" for r in D['companies'])
sources='\n'.join(f"- [{s['name']}]({s['url']}): 목록 {s['listed_jobs']}개, robots 판정 `{s['robots']['decision']}`." for s in D['collection'])
text=f'''# AI, Now Hiring?

**광고·마케팅 직군 채용공고의 AI 역량 요구·우대 명시 비율** — 데이터 리터러시 중간고사 / THE HIRING SIGNAL.

발표 URL: **https://ancoded1234.github.io/advertising-ai-hiring-analysis/**

GitHub: https://github.com/ancoded1234/advertising-ai-hiring-analysis

## 연구 질문과 실제 결론

광고대행사는 채용공고에서 AI 역량을 얼마나 명시할까? AE/기획, 카피라이터, 디자인/영상, 퍼포먼스 직무를 비교했다. 색상 분석 프로젝트와 독립된 새 프로젝트이며 이전 프로젝트를 수정하지 않았다.

**6개 공식 채용페이지의 목록 {A['listed_records']}개를 수집하고 {T['n']}개를 분석했다.** 자격요건·우대사항에 명시적 생성형 AI/도구명을 언급한 공고는 **{T['genai']}/{T['n']} ({P(T['rate'])})**, 일반적인 AI 관심·활용 표현까지 포함하면 **{T['broad_ai']}/{T['n']} ({P(T['broad_rate'])})**다. 이 비율은 조사한 편의 표본의 기술통계이며 한국 광고 채용시장 전체의 요구율이 아니다.

|직무|분모|생성형 AI 명시|비율|포괄 AI 포함|비율|
|---|---:|---:|---:|---:|---:|
{role_table}

카피라이터의 0건은 AI 역량이 불필요하다는 근거가 아니다. 표본이 2개뿐이다. 특정 기업의 채용 문구와 공고 구성에 따라 비율이 달라지고, 명시하지 않은 기업이 실제로 AI를 사용하지 않는다는 뜻도 아니다. 단일 시점이므로 AI 요구가 과거보다 증가했다고 주장하지 않는다.

## 수집 범위와 접근 제한

수집일: **{A['collected_at'][:10]}**, 현재 목록에 게시된 공고를 스냅샷으로 관찰했다. 기업 공개 채용페이지를 접근 가능성과 광고·마케팅 업무 관련성에 따라 편의 선정했다. 공고 내용의 AI 유무로 기업이나 공고를 뽑지 않았다. 초기 탐색용 검색·API 응답은 분석 분모에 합치지 않았다.

{sources}

원티드 공개 API는 테스트에서 HTTP 200을 반환했지만, 원티드 개인회원 이용약관에서 사전 허락 없는 자동화 수집 제한을 확인해 대량 수집을 중단했다. 사람인 직접 요청은 오류 안내, 잡코리아 직접 요청은 HTTP 200인 보안정책 HTML을 반환했다. 이를 공고 수집 성공으로 기록하지 않았다. `results/platform_access.json`에 시도와 제외 이유를 보관했다. 대신 robots 정책상 공개 채용 URL을 읽을 수 있는 공식 기업 페이지를 사용했다. 로그인·지원서·개인회원 프로필·캡차·우회 프록시는 사용하지 않았다. robots의 공개 허용이 원문 재배포 허가를 의미하지 않으므로 원문은 공개하지 않는다.

수집 도구: `requests`, BeautifulSoup, 공개 페이지의 정상 브라우저 렌더링(Playwright). PDF는 PyMuPDF, 이미지 공고는 **Windows.Media.Ocr 한국어 엔진**을 사용했다. Firecrawl은 배경 문헌과 원문 교차확인에 사용했다.

## 정제 / 분모

- 목록 공고 {A['listed_records']}개, 고유 URL {A['unique_urls']}개. URL 중복 0개.
- 비대상 직무 12개(개발·데이터·회계·총무·웹기획 등), 마감 공고 1개, 인재풀·비공고 3개 제외 → {T['n']}개.
- 채용페이지에 현재 게시되어 있고, 목표 직무이며, 자격요건을 판독할 수 있는 공고를 분모로 삼았다. 현재 채용 중이라는 기업 HR의 별도 확인을 받은 것은 아니다.
- 공고 단위 분석이다. 한 공고가 몇 명을 채용하는지와 무관하게 1개로 센다. 동일 기업의 문구 반복과 별도 경력 수준 포지션은 제거하지 않으므로 관측값의 독립성을 보장하지 않는다.
- 분석 표본 중 이미지 OCR {A['ocr_postings']}개. 이미지 OCR 읽기 순서·문자 손상 2건과 직무 오분류 1건은 원문/직무 대조 후 `data/review_decisions.json`에 근거를 기록했다. 신입·경력 Creative PD 두 공고는 별도 URL·포지션이므로 유지했다.

## 코드북 / 무엇을 AI 요구로 셌나?

주요 지표는 ‘능력의 실제 필수 여부’가 아니라 **자격요건 또는 우대사항 섹션의 명시 여부**다. 단순 관심을 찾는 문구도 해당 섹션에 있다면 표현 강도를 별도로 설명한다.

1. **엄격 기준:** `생성형 AI`, `Generative AI`, GenAI 또는 명시적 생성형 도구명/계열을 요건·우대에서 발견. ChatGPT/GPT/GPTs, Midjourney, Stable Diffusion/ComfyUI, Runway, Claude, Gemini, DALL·E, Firefly, Kling, Sora, Copilot, Perplexity, Nano Banana, Higgsfield 등을 코드북에 포함했다.
2. **포괄 기준:** 엄격 기준 + 도구명 없는 AI 활용·경험·관심·AI Image/Video Tool 등 일반 AI 표현. 생성형 AI로 한정되지 않아 엄격 기준과 섞지 않는다.
3. 회사소개, 주요업무, 복리후생의 언급은 두 주요 비율에서 제외. 본문 전체의 생성형 AI 언급은 별도 집계했다. 본문 전체에서만 보면 {A['anywhere_genai']}개이며, 그중 {A['genai_only_elsewhere']}개는 요건·우대에 생성형 AI 표현이 없다.
4. Adobe Creative Suite의 `Ai, Ps`에서 Ai는 Illustrator이므로 AI로 세지 않는다. 한국어 `달리`라는 일반 부사는 DALL·E로 잡지 않는다. `CHAI`에 들어 있는 AI도 잡지 않는다.
5. 동일 공고에서 반복·복수 도구는 전체 명시율에 한 번만 센다. 도구별 집계는 도구당 공고 1회이며 공고 간/도구 간 중복이 허용되어 합계가 전체 명시 공고 수와 다르다.
6. 직무는 카피라이터 → 퍼포먼스 → 디자인/영상 → AE/기획 순으로 제목의 구체적인 직무 신호를 우선 적용해 상호 배타적으로 분류했다. AE/기획은 일반·콘텐츠 마케터, 매체·프로모션 기획까지 포함한다. 이미지의 실제 직무가 Creative PD인 2건은 본문에 따라 디자인/영상으로 교정했다. ‘프로모션’의 부분문자열 ‘모션’은 영상 직무로 판정하지 않는다.

분류는 AI Agent가 규칙 코딩과 원문 대조로 수행했다. 독립된 2인 블라인드 라벨링이나 외부 정답셋이 없으므로 분류 정확도·Precision·Recall을 보고하지 않는다. 이 질문에 불필요한 예측 모델을 만들지 않았다.

## 결과의 세부 해석

엄격 기준: 자격요건 {T['required']}개, 우대사항 {T['preferred']}개, 양쪽 모두 {T['both']}개 → 합집합 {T['required']}+{T['preferred']}-{T['both']}={T['genai']}개.

|기업 채용페이지|분석 공고|생성형 AI 명시|포괄 AI 포함|
|---|---:|---:|---:|
{company_table}

기업 채용페이지를 하나씩 제외했을 때 엄격 명시율은 **{P(min(x['rate'] for x in D['leave_one_company_out']))}~{P(max(x['rate'] for x in D['leave_one_company_out']))}**였다. 기업 구성에 민감한 작은 표본이다. Wilson 95% 구간은 이항모형의 참고치로만 제시하며, 편의·기업 군집 표본의 시장 모수 신뢰구간이나 직무 간 유의성 검정으로 해석하지 않는다.

요건·우대에서 GPT 계열이 잡힌 1건은 **GPTs** 표현이다. ChatGPT 직접 언급 1건으로 바꾸어 말하면 안 된다. Stable Diffusion·Runway는 이 표본에서 0건이며 시장 전체에 수요가 없다는 뜻이 아니다.

### 디자인 전공 학생에게 주는 시사점

AI 도구 이름을 나열하는 것뿐 아니라, 광고 목표·타깃·콘셉트와 도구를 사용한 이유, 프롬프트·반복 수정·최종 선택 근거를 작업 과정으로 남겨볼 수 있다. 다만 이는 관찰된 공고 문구를 바탕으로 한 제안이며 취업 성공 효과를 실험한 결과는 아니다.

## Firecrawl / 배경 문헌

기존 상위 `.env`만 `python-dotenv`로 `override=False` 로딩했다. 새 `.env`는 만들지 않았으며 키 값은 출력·업로드하지 않는다. Firecrawl v2 API 성공과 원본 metadata.statusCode=200을 함께 검증했다.

- [ILO, Generative AI and Jobs (2025)](https://www.ilo.org/publications/generative-ai-and-jobs-refined-global-index-occupational-exposure): 업무별 AI 노출과 직무 변화의 배경. 노출도는 공고 명시율이나 일자리 소멸률이 아니다.
- [WEF, The Future of Jobs Report 2025](https://www.weforum.org/publications/the-future-of-jobs-report-2025/): 글로벌 고용주의 기술·직무 변화 전망. 한국 광고업의 현재 비율과 직접 비교하지 않는다.
- [디자인피버 AI 영상 크리에이터 공고](https://careers.designfever.com/job-opening/88): 원문 교차확인. 주요업무와 요건의 표현을 분리했다.
- [차이커뮤니케이션 광고 디자이너 공고](https://chai.career.greetinghr.com/ko/o/239857): 이미지 본문/Adobe Ai 오탐 확인 대상.

`data/firecrawl/research_sources.json`에 4건의 정상 수집을 기록했다. `sources.json`에는 초기 정책 확인과 실패도 남겼다. 일시적인 Firecrawl 429는 제공된 재시도 시간을 지킨 후 재시도했다. 원문 전문은 로컬 `*_full.json`이며 Git에서 제외한다.

## 재현 / 실행

현재 환경: **Windows, Python 3.12, 한국어 Windows OCR 언어 팩**. 패키지 버전은 `requirements.txt`에 고정했다. OCR은 이 Windows 환경에 의존하며 다른 OS에서는 승인된 한국어 OCR로 대체하거나 이미지 공고를 판독 불가로 남겨야 한다. 읽지 못한 공고를 음성으로 넣지 말 것.

```powershell
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
.venv/Scripts/python.exe -m playwright install chromium
.venv/Scripts/python.exe scripts/collect.py
.venv/Scripts/python.exe scripts/ocr.py
.venv/Scripts/python.exe scripts/background.py
.venv/Scripts/python.exe scripts/analyze.py
.venv/Scripts/python.exe scripts/figures.py
.venv/Scripts/python.exe scripts/document.py
.venv/Scripts/python.exe scripts/verify.py
.venv/Scripts/python.exe -m http.server 8766 --directory docs
```

브라우저 검증(서버가 실행된 다른 터미널):

```powershell
.venv/Scripts/python.exe scripts/qa.py http://localhost:8766
```

공고는 수시로 마감·변경되므로 재수집 시 수치가 달라질 수 있다. 원본 HTML/PDF/이미지와 추출 본문은 로컬 캐시, 공개 자료는 당시 URL·시각·판정·집계 스냅샷이다. 엄격·포괄 기준은 코드에 명시돼 있으며 수동 교정은 URL 해시 ID에 연결되어 있다. 재수집된 동일 URL의 내용이 바뀌면 기존 수동 교정을 다시 확인해야 한다.

## 파일 구성

```text
data/raw/                        # HTML/PDF/이미지·OCR·전체 섹션 검토 (Git 제외)
data/firecrawl/                  # 출처 기록, 전문은 Git 제외
data/review_decisions.json       # 원문 근거가 있는 교정 기록
scripts/collect.py               # 공식 공개 채용페이지 수집
scripts/ocr.py                   # 이미지 공고 한국어 OCR
scripts/analyze.py               # 섹션 분리, 코드북, 집계
scripts/background.py            # Firecrawl 문헌·교차확인
scripts/figures.py               # 공유 가능한 통계 그래프 PNG/SVG
scripts/verify.py                # 분모/분자·오탐·섹션 경계·키 노출 검사
scripts/qa.py                    # 4개 화면 × 12장, 인터랙션 검증
results/coded_postings.csv       # 수집한 45개 공고와 포함/제외·판정
results/role_summary.csv         # 직무별 비교
results/company_summary.csv      # 기업별 구성
results/tool_counts.csv          # 용어별 공고 수
results/analysis.json            # 집계, 사례, 기업제외 민감도
results/collection_manifest.json # 수집 URL·robots·시각
results/platform_access.json     # 플랫폼 접근 제한과 제외 이유
results/figures/                 # 실제 데이터 그래프
docs/index.html                  # GitHub Pages 12장 발표자료
docs/assets/                     # CSS/JS
docs/data/analysis.json          # 발표자료가 직접 읽는 실측 데이터
```

공개 JSON은 원문당 짧은 발췌 하나와 공고 메타데이터만 담는다. 전체 본문·원본 이미지·개인 연락처·지원서·API 키·인증 파일은 공개하지 않는다.

## 발표 조작 / 검증 / 배포

- 좌우 방향키·PageUp/PageDown·Home/End, 이전/다음 버튼, 페이지 번호·진행률, F/전체 화면.
- 데스크톱 16:9, 모바일·태블릿에서는 내용을 세로로 확장해 표시한다.
- ‘생성형 AI 명시’ / ‘포괄 AI 포함’ 전환으로 동일한 공고에 다른 정의를 적용한 결과를 비교한다.
- 사각형 1개=공고 1개. 클릭하면 원문 근거를 탐색한다. 기업/제목 검색, 직무·AI 판정 필터와 CSV 내려받기를 제공한다.
- `results/browser_qa.json`은 브라우저 검증 기록, `results/data_validation.json`은 분석·오탐 회귀 검사, `results/deployment.json`은 공개 HTTP·정적 자산 일치 검증 기록이다.
- GitHub CLI로 독립 공개 저장소를 생성하고 main을 push한다. 공식 Pages REST API로 source=main, path=/docs를 설정한다. 상대 경로와 `.nojekyll`을 사용한다.

**제출용 발표 URL: https://ancoded1234.github.io/advertising-ai-hiring-analysis/**
'''
(R/'README.md').write_text(text,encoding='utf-8');print('README generated from measured artifacts.')
