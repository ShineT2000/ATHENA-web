# ATHENA 연구실 웹사이트

내용(`data/`, `pages/`)과 디자인(`templates/`, `static/`)을 분리한 새 구조입니다.
https://athena.hanyang.ac.kr/ (Google Sites)의 20개 페이지를 옮겨 온 정적 사이트입니다. `python build.py` 한 번으로 `dist/`에 완성된 사이트가 만들어집니다.

## 무엇을 고치려면 어느 파일을?

| 고칠 내용 | 파일 |
|---|---|
| 메인 뉴스 | `data/news.toml` (뉴스 사진은 `static/img/news/`) |
| 메인 JOIN US 문구 | `pages/home-join.html` |
| 메인 첫 화면 문구 | `data/site.toml`의 `/main` 항목 (`subtitle`, `tagline`) |
| 저널·학회 논문 | `data/journal.csv`, `data/conference.csv` |
| 수상 | `data/awards.csv` (`year`, `award` 두 칸) |
| 구성원·졸업생 | `data/people/*.toml` (사진은 `static/img/people/`) |
| 연구 분야 4개 | `pages/research/*.html` (그림은 `static/img/pages/`) |
| 연락처·지도 | `pages/contact-us.html` |
| 메뉴 이름·순서, 페이지 목록 | `data/site.toml` |
| 색상·글꼴·간격 | `static/css/style.css` (맨 위 `:root` 변수) |

## 빌드와 미리보기

이 폴더(ATHENA-website)에서:

```powershell
python build.py
python -m http.server 4173 --bind 127.0.0.1 --directory dist
```

브라우저에서 http://127.0.0.1:4173/ 을 엽니다. Python 3.11 이상만 있으면 되고, 추가 설치는 필요 없습니다.

## 논문 추가·수정: `data/journal.csv`, `data/conference.csv`

두 파일의 형식은 같습니다.

| 칸 | 내용 |
|---|---|
| `year` | 연도. 이 값으로 자동으로 묶이고, 최신 연도가 위로 정렬됩니다. 새 연도도 그냥 쓰면 됩니다. |
| `citation` | 화면에 보일 인용문 그대로. `*기울임*`, `**굵게**`, `^위첨자^`(예: `7^th^`) 표기를 쓸 수 있습니다. 교신저자 표시 같은 별표 자체는 `\*`로 씁니다(예: `Sung Joong Kim\*`). |
| `url` | 논문 링크(DOI 등). 비워 두면 링크 없이 표시됩니다. |

같은 연도 안에서는 **파일에 적힌 순서대로** 표시되므로, 새 논문은 해당 연도의 맨 위 줄에 넣으세요.

**Excel로 편집할 때:** 저장할 때 파일 형식을 반드시 **"CSV UTF-8(쉼표로 분리)"**로 고르세요.
일반 "CSV (쉼표로 분리)"는 날짜 범위의 대시(May 6–8의 –)나 악센트 문자(ó) 같은 글자를 `?`로 바꿉니다. 학회 목록에서는 45편이 해당됩니다. 이 경우 빌드할 때 경고가 표시됩니다.

## 구성원 추가·수정: `data/people/*.toml`

페이지마다 파일이 하나씩 있습니다(`graduate-students.toml`, `alumni.toml` 등). 한 사람은 이런 블록 하나입니다.

```toml
[[group.person]]
name = "Hong Gildong"
photo = "hong-gildong.jpg"
email = "hong@hanyang.ac.kr"
education = [
  "B.S. Nuclear Engineering, Hanyang University, 2026",
]
research = [
  "Severe accident analysis",
]
```

- **새 학생 추가:** 비슷한 사람의 블록을 복사해 원하는 위치에 붙여 넣고 내용을 고칩니다. 화면에는 파일 순서대로 나옵니다.
- **사진:** `static/img/people/`에 넣고 파일 이름만 적습니다(영문·숫자·하이픈 권장). 사진이 없으면 `photo` 줄을 지웁니다.
- **그룹:** `[[group]]`(예: Ph.D. Candidates, M.S. Students) 아래의 `[[group.person]]`은 그 그룹에 속합니다. 그룹이 없는 파일은 `[[person]]`을 씁니다.
- **졸업 처리:** 대학원생 파일에서 블록을 지우고, `alumni.toml`의 알맞은 그룹에 다음 형식으로 추가합니다.

```toml
[[group.person]]
name = "Hong Gildong"
degree = "M.S (2027)"
thesis = "논문 제목"
position = "KAERI"
```

- **칸 이름:** `education`(학력), `experience`(경력), `research`(연구 분야), `lines`(제목 없는 자유 문단. 빈 문자열 `""`은 문단 구분)
- **입학 연월·키워드:** `since = "2026.03"`은 이름 옆에 `(2026.03~)`로, `keywords = ["MSR", "CFD"]`는 연구 분야 아래 `KEY WORD #MSR #CFD`로 표시됩니다. 둘 다 없으면 줄을 지우면 됩니다.
- **기간 열 맞추기:** `"2011~2017 | Assistant Professor"`처럼 ` | `로 나누면 기간과 내용이 열로 정렬됩니다.
- **제목 표기(Education 또는 EDUCATION)와 사진 크기:** `site.toml`에서 페이지의 `style` 값(`professor`, `student`, `plain`)으로 정해집니다.
- 따옴표나 쉼표가 빠지는 등 형식이 틀리면 빌드할 때 몇 번째 줄인지 알려 줍니다.

## 뉴스 추가: `data/news.toml`

맨 위에 있는 뉴스가 먼저 보입니다. 새 소식은 파일 맨 위(설명 주석 아래)에 추가합니다.

```toml
[[news]]
date = "October 1, 2026"
title = "Hong Gildong - Won the Best Paper Award (KNS)"
photo = "2026-10-best-paper.jpg"      # 선택. static/img/news/ 에 넣은 사진
background = "beige"                  # 선택. 생략(흰색) / "beige" / "brown"
body = [
  "Congratulations to Hong Gildong on winning the Best Paper Award.",
  "**Research Period**: 2026.10.01 – 2030.12.31",
]
```

메인 첫 화면의 "Last modified" 날짜는 `data/`와 `pages/`에서 가장 최근에 고친 파일 날짜로 자동 표시됩니다.

## 글 위주 페이지 고치기: `pages/*.html`

연구 분야와 연락처는 간단한 HTML입니다. 주제 하나는 이런 모양입니다.

```html
<section class="topic cols-2">
  <div class="col">                        <!-- 왼쪽: 제목과 그림 -->
    <h2>i-SMR <small>(innovative Small Modular Reactor)</small></h2>
    <div class="carousel" style="aspect-ratio: 0.904">   <!-- 사진 여러 장 = 슬라이드 -->
      <img src="/static/img/pages/smr-5.png" alt="">
      <img src="/static/img/pages/smr-6.png" alt="">
    </div>
  </div>
  <div class="col">                        <!-- 오른쪽: 설명 -->
    <h3>introduction</h3>
    <p>문단은 &lt;p&gt;, <strong>굵게</strong>, 목록은 &lt;ul&gt;&lt;li&gt;</p>
    <p>1) 논문 제목<br><a href="https://doi.org/..." target="_blank" rel="noopener">Published article (2026)</a></p>
  </div>
</section>
```

- 사진 한 장은 `<div class="carousel">` 없이 `<img>`만 씁니다.
- 새 주제는 `<section>…</section>` 블록을 통째로 복사해 고칩니다.

## 폴더 구성

```
ATHENA-website/
  build.py            빌드 스크립트
  data/site.toml      메뉴, 사이트 이름, 페이지 목록(페이지마다 종류 type 지정)
  data/news.toml      메인 뉴스
  data/journal.csv    저널 논문
  data/conference.csv 학회 발표
  data/awards.csv     수상
  data/people/*.toml  구성원 (페이지별 파일)
  pages/              글 위주 페이지 본문 (JOIN US, 연구 분야, 연락처)
  templates/base.html 모든 페이지 공통 틀 (메뉴, 배너, 검색창)
  static/css/style.css  디자인. 색상·글꼴은 맨 위 :root 변수에서 바꿉니다.
  static/js/site.js     메뉴, 검색 등 동작
  static/fonts, img     글꼴, 로고, 배너(img/banner.jpg), 구성원(img/people), 뉴스(img/news), 연구 그림(img/pages)
  dist/               빌드 결과 (직접 고치지 마세요. 빌드마다 새로 만들어집니다.)
```

## 배포 (GitHub Pages)

`main` 브랜치에 올리면(`git push`) GitHub가 자동으로 빌드해 배포합니다(`.github/workflows/deploy.yml`). 1~2분 걸리며, 진행 상황은 저장소의 **Actions** 탭에서 볼 수 있습니다.

```powershell
git add -A
git commit -m "뉴스 추가: ..."
git push
```

- 사이트 주소: `https://<GitHub 계정>.github.io/<저장소 이름>/`
- 처음 한 번만: 저장소 **Settings → Pages → Build and deployment → Source**를 **GitHub Actions**로 설정합니다.
- 배포가 실패하면 Actions 탭의 빨간 ✗ 항목을 열어 보세요. `[오류]`로 시작하는 줄에 어느 파일 몇 번째 줄이 문제인지 나옵니다.
- **자체 도메인(예: athena.hanyang.ac.kr) 연결:** Settings → Pages → Custom domain에 도메인을 적고, 학교 DNS 관리자에게 `CNAME` 레코드를 `<GitHub 계정>.github.io`로 요청합니다. 경로는 자동으로 맞춰집니다.
- 다른 곳에 올릴 때는 `dist/` 폴더 전체를 올리면 됩니다. 하위 경로에 올린다면 빌드 전에 `SITE_BASE`를 지정합니다(예: PowerShell에서 `$env:SITE_BASE="/athena"; python build.py`).

## 수정 이력 (Git)

이 폴더는 Git으로 관리됩니다. 고친 뒤에는 이력을 남겨 두세요.

```powershell
git status                          # 무엇이 바뀌었는지 보기
git add -A
git commit -m "뉴스 추가: 2026년 10월 학회 수상"
git log --oneline                   # 이력 보기
git restore data/news.toml          # 아직 커밋하지 않은 수정 되돌리기
```

`dist/`(빌드 결과)는 매번 새로 만들어지므로 Git에 넣지 않습니다(`.gitignore`). GitHub가 배포할 때 직접 빌드합니다.
