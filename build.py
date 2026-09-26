"""ATHENA 웹사이트 빌드: data/ 의 내용 + templates/ 의 틀 → dist/ 의 완성된 사이트.

실행:  python build.py
미리보기:  python -m http.server 4173 --bind 127.0.0.1 --directory dist

외부 패키지 없이 Python 3.11 이상만 있으면 됩니다.
"""
import csv
import html
import html.parser
import json
import os
import re
import shutil
import stat
import sys
import tomllib
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DIST = ROOT / "dist"
# 사이트가 도메인의 하위 경로에 올라갈 때의 기준 경로 (예: GitHub Pages 의 "/ATHENA-website").
# 비워 두면 도메인 최상위(/) 기준입니다. GitHub Actions 가 자동으로 넣어 줍니다.
BASE = os.environ.get("SITE_BASE", "").rstrip("/")


def fail(message):
    sys.exit(f"\n[오류] {message}\n")


def clear_readonly(path):
    os.chmod(path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)


def retry_writable(function, path, _error):
    """Windows는 '읽기 전용' 폴더·파일을 지우지 못하므로 속성을 풀고 다시 시도합니다."""
    clear_readonly(path)
    function(path)


# ── 데이터 읽기 ───────────────────────────────────────────

def read_csv(path):
    """CSV를 읽습니다. Excel이 한글 Windows에서 저장한 파일(cp949)도 읽을 수 있습니다."""
    if not path.exists():
        fail(f"{path.relative_to(ROOT)} 파일이 없습니다.")
    for encoding in ("utf-8-sig", "cp949"):
        try:
            with path.open(encoding=encoding, newline="") as f:
                rows = list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
        if encoding == "cp949":
            print(f"  [주의] {path.name}이(가) Excel의 'CSV (쉼표로 분리)' 형식으로 저장되었습니다.\n"
                  "         이 형식은 일부 특수문자(날짜의 – 대시, ó 같은 악센트 문자 등)를 ?로 바꿉니다. 'CSV UTF-8(쉼표로 분리)'로 다시 저장해 주세요.")
        return rows
    fail(f"{path.name}의 글자 인코딩을 읽을 수 없습니다. UTF-8로 저장해 주세요.")


def year_key(year):
    """'2026', '~2009' 같은 연도 표기를 정렬용 숫자로 바꿉니다."""
    digits = re.sub(r"\D", "", year)
    return int(digits) if digits else 0


# ── 서식 ─────────────────────────────────────────────────

def format_citation(text):
    """인용문을 HTML로 바꿉니다. **굵게**, *기울임*, ^위첨자^ 표기를 지원하고, \\* 는 별표 그대로 씁니다."""
    text = html.escape(text.replace(r"\*", "\x00"))
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"\^(.+?)\^", r"<sup>\1</sup>", text)
    return text.replace("\x00", "*")


def plain_text(text):
    return re.sub(r"[*^]", "", text.replace(r"\*", "\x00")).replace("\x00", "*")


# ── 페이지 종류별 본문 ────────────────────────────────────

def render_publications(page):
    """연도별로 접고 펼 수 있는 논문 목록. 같은 연도 안에서는 CSV의 순서를 따릅니다."""
    rows = read_csv(DATA / page["data"])
    years = {}
    for line, row in enumerate(rows, start=2):
        year = (row.get("year") or "").strip()
        citation = (row.get("citation") or "").strip()
        if not year and not citation:
            continue  # 빈 줄
        if not year or not citation:
            fail(f"{page['data']} {line}번째 줄: year와 citation을 모두 채워 주세요.")
        years.setdefault(year, []).append({"citation": citation, "url": (row.get("url") or "").strip()})

    parts, search_text = [], []
    for year in sorted(years, key=year_key, reverse=True):
        items = []
        for item in years[year]:
            cite = format_citation(item["citation"])
            if item["url"]:
                cite = f'<a href="{html.escape(item["url"])}" target="_blank" rel="noopener">{cite}</a>'
            items.append(f"          <li>{cite}</li>")
            search_text.append(plain_text(item["citation"]))
        anchor = "y" + re.sub(r"\W", "", year)
        parts.append(
            f'      <details class="pub-year" id="{anchor}">\n'
            f'        <summary><h2>{html.escape(year)}</h2></summary>\n'
            f'        <ul>\n' + "\n".join(items) + "\n        </ul>\n"
            f"      </details>"
        )
    return {"body": "\n".join(parts), "text": " ".join([*years, *search_text])}


# 구성원 카드의 제목 표기와 모양. site.toml 의 style 값으로 고릅니다.
PEOPLE_STYLES = {
    # 교수: 큰 사진, 경력·연구분야는 글머리표 목록
    "professor": {"photo": "large", "labels": {"education": "Education", "experience": "Professional Experiences", "research": "Research Field"},
                  "lists": {"experience", "research"}},
    # 학생: 작은 사진(없어도 같은 자리 비움), 제목은 대문자
    "student": {"photo": "small", "labels": {"education": "EDUCATION", "experience": "EXPERIENCE", "research": "RESEARCH INTEREST"},
                "lists": set()},
    # 사진 자리 없이 이름·이메일만
    "plain": {"photo": None, "labels": {"education": "Education", "experience": "Experience", "research": "Research"}, "lists": set()},
}


def read_toml(relative):
    path = DATA / relative
    if not path.exists():
        fail(f"{relative} 파일이 없습니다.")
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        fail(f"{relative}의 형식이 올바르지 않습니다: {error}\n"
             "따옴표(\")나 쉼표, [[person]] 줄이 빠지지 않았는지 확인해 주세요.")


def groups_of(data):
    """[[person]] 만 있는 파일과 [[group]] 으로 묶인 파일을 같은 모양으로 맞춥니다."""
    if "group" in data:
        return [{"title": g.get("title", ""), "people": g.get("person", []), "divider_after": g.get("divider_after", False)}
                for g in data["group"]]
    return [{"title": "", "people": data.get("person", []), "divider_after": False}]


def esc(text):
    return html.escape(text or "")


def period_line(text):
    """'2011~2017 | Assistant Professor' 처럼 | 로 나눈 줄은 기간 열을 맞춰 표시합니다."""
    if " | " in text:
        period, rest = text.split(" | ", 1)
        return f'<span class="cols"><span class="period">{esc(period)}</span><span>{esc(rest)}</span></span>'
    return esc(text)


def render_person(person, style, where):
    for key in ("name",):
        if not person.get(key):
            fail(f"{where}: name(이름)이 비어 있는 사람이 있습니다.")
    parts = []
    if style["photo"]:
        photo = person.get("photo")
        if photo and not (ROOT / "static" / "img" / "people" / photo).exists():
            fail(f"{where} '{person['name']}': 사진 파일 static/img/people/{photo} 이(가) 없습니다.")
        img = f'<img src="/static/img/people/{esc(photo)}" alt="{esc(person["name"])}" loading="lazy">' if photo else ""
        parts.append(f'<div class="person-photo">{img}</div>')

    since = f' <span class="person-since">({esc(person["since"])}~)</span>' if person.get("since") else ""
    info = [f'<h3 class="person-name">{esc(person["name"])}{since}</h3>']
    if person.get("lines"):
        paragraphs, current = [], []
        for line in person["lines"] + [""]:
            if line:
                current.append(f'<span class="line">{period_line(line)}</span>')
            elif current:
                paragraphs.append("<p>" + "".join(current) + "</p>")
                current = []
        info.append('<div class="person-lines">' + "".join(paragraphs) + "</div>")
    for key in ("education", "experience", "research"):
        items = person.get(key)
        if not items:
            continue
        items = [items] if isinstance(items, str) else items
        info.append(f'<h4 class="person-label">{style["labels"][key]}</h4>')
        if key in style["lists"]:
            info.append('<ul class="person-list">' + "".join(f"<li>{period_line(i)}</li>" for i in items) + "</ul>")
        else:
            info.append('<div class="person-text">' + "".join(f'<p class="line">{period_line(i)}</p>' for i in items) + "</div>")
    if person.get("keywords"):
        tags = " ".join(f"#{esc(k)}" for k in person["keywords"])
        info.append(f'<p class="person-keywords">{tags}</p>')
    if person.get("email"):
        info.append(f'<a class="person-email" href="mailto:{esc(person["email"])}">{esc(person["email"])}</a>')
    parts.append('<div class="person-info">' + "".join(info) + "</div>")
    photo_class = f' photo-{style["photo"]}' if style["photo"] else ""
    return f'        <article class="person{photo_class}">' + "".join(parts) + "</article>"


def person_text(person):
    values = [person.get(k, "") for k in ("name", "degree", "thesis", "position", "email")]
    for key in ("lines", "education", "experience", "research", "keywords"):
        items = person.get(key) or []
        values += [items] if isinstance(items, str) else [i.replace(" | ", " ") for i in items]
    return " ".join(v for v in values if v)


def render_people_groups(groups, render_one):
    parts, text = [], []
    for group in groups:
        block = []
        if group["title"]:
            block.append(f'        <h2 class="group-title">{esc(group["title"])}</h2>')
            text.append(group["title"])
        block += [render_one(p) for p in group["people"]]
        text += [person_text(p) for p in group["people"]]
        parts.append('      <section class="people-group">\n' + "\n".join(block) + "\n      </section>")
        if group["divider_after"]:
            parts.append('      <hr class="divider">')
    return {"body": "\n".join(parts), "text": " ".join(text)}


def render_people(page, site):
    style = PEOPLE_STYLES.get(page.get("style", "student"))
    if not style:
        fail(f"{page['url']}: style 은 {', '.join(PEOPLE_STYLES)} 중 하나여야 합니다.")
    groups = groups_of(read_toml(page["data"]))
    return render_people_groups(groups, lambda p: render_person(p, style, page["data"]))


def render_alumni(page, site):
    def one(person):
        if not person.get("name"):
            fail(f"{page['data']}: name(이름)이 비어 있는 사람이 있습니다.")
        head = f'<strong>{esc(person["name"])}</strong>' + (f", {esc(person['degree'])}" if person.get("degree") else "")
        items = []
        if person.get("thesis"):
            items.append(f"<li>Thesis: {esc(person['thesis'])}</li>")
        if person.get("position"):
            items.append(f"<li>Present Position - {esc(person['position'])}</li>")
        items += [f"<li>{esc(n)}</li>" for n in person.get("notes", [])]
        return (f'        <article class="alumnus"><h3 class="person-name">{head}</h3>'
                + (f'<ul class="person-list">{"".join(items)}</ul>' if items else "") + "</article>")
    return render_people_groups(groups_of(read_toml(page["data"])), one)


def render_hub(page, site):
    """하위 페이지로 가는 버튼 목록 (메뉴의 하위 항목을 그대로 사용)."""
    entry = next((m for m in site["menu"] if m["url"] == page["url"]), None)
    children = entry.get("children", []) if entry else []
    buttons = "".join(f'<a class="hub-button" href="{c["url"]}">{esc(c["title"])}</a>' for c in children)
    return {"body": "", "text": " ".join(c["title"] for c in children),
            "banner_class": "banner banner-full", "banner_extra": f'      <nav class="hub" aria-label="{esc(page["title"])}">{buttons}</nav>'}


def render_awards(page, site):
    """연도별 수상 목록 (접기 없음). 같은 연도 안에서는 CSV 순서를 따릅니다."""
    years = {}
    for line, row in enumerate(read_csv(DATA / page["data"]), start=2):
        year, award = (row.get("year") or "").strip(), (row.get("award") or "").strip()
        if not year and not award:
            continue
        if not year or not award:
            fail(f"{page['data']} {line}번째 줄: year와 award를 모두 채워 주세요.")
        years.setdefault(year, []).append(award)
    parts = []
    for year in sorted(years, key=year_key, reverse=True):
        items = "".join(f"<li>{format_citation(a)}</li>" for a in years[year])
        parts.append(f'        <h2 class="award-year">{esc(year)}</h2>\n        <ul class="award-list">{items}</ul>')
    text = " ".join(f"{y} " + " ".join(plain_text(a) for a in years[y]) for y in years)
    return {"body": '      <div class="awards">\n' + "\n".join(parts) + "\n      </div>", "text": text}


class TextOnly(html.parser.HTMLParser):
    """검색 색인용으로 HTML에서 글자만 뽑습니다."""
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def render_html(page, site):
    """글 위주 페이지: pages/ 폴더의 HTML 조각을 그대로 본문에 넣습니다."""
    path = ROOT / "pages" / page["file"]
    if not path.exists():
        fail(f"pages/{page['file']} 파일이 없습니다.")
    body = path.read_text(encoding="utf-8")
    reader = TextOnly()
    reader.feed(body)
    result = {"body": body, "text": " ".join(" ".join(reader.parts).split())}
    if page.get("banner") is False:  # 배너 사진 없이 제목만
        result["banner_class"] = "banner banner-none"
    return result


def last_modified():
    """data/·pages/ 안에서 가장 최근에 고친 파일의 날짜 (메인 화면의 'Last modified')."""
    import datetime
    import subprocess
    day = None
    if os.environ.get("GITHUB_ACTIONS"):
        # GitHub 서버에서는 파일을 매번 새로 받으므로 수정 시각 대신 마지막 커밋 날짜를 씁니다.
        try:
            out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", "data", "pages"],
                                 cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
            day = datetime.date.fromisoformat(out) if out else None
        except (OSError, subprocess.CalledProcessError, ValueError):
            day = None
    if day is None:
        files = [p for folder in (DATA, ROOT / "pages") for p in folder.rglob("*") if p.is_file()]
        day = datetime.date.fromtimestamp(max(p.stat().st_mtime for p in files))
    return f"{day:%B} {day.day}, {day.year}"


def render_home(page, site):
    """메인: 화면 전체 첫 화면 + JOIN US(pages/ HTML) + NEWS(data/news.toml)."""
    hero = (f'      <p class="hero-subtitle">{format_citation(page["subtitle"]).replace(chr(10), "<br>")}</p>\n'
            f'      <p class="hero-tagline">{esc(page.get("tagline", ""))}</p>\n'
            f'      <p class="hero-updated">Last modified: {last_modified()}</p>\n'
            '      <button class="scroll-down" type="button" aria-label="Scroll down">'
            '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M16.59 8.59 12 13.17 7.41 8.59 6 10l6 6 6-6z"/></svg></button>')
    join = render_html({"file": page["join"]}, site)
    news = read_toml(page["news"]).get("news", [])
    items, text = [], [join["text"]]
    for n, item in enumerate(news, start=1):
        if not item.get("title") or not item.get("date"):
            fail(f"{page['news']}: {n}번째 뉴스에 date 또는 title 이 없습니다.")
        classes = ["news-item"]
        photo = ""
        if item.get("photo"):
            if not (ROOT / "static/img/news" / item["photo"]).exists():
                fail(f"{page['news']} '{item['title']}': 사진 static/img/news/{item['photo']} 이(가) 없습니다.")
            classes.append("has-photo")
            photo = f'<img src="/static/img/news/{esc(item["photo"])}" alt="" loading="lazy">'
        if item.get("background"):
            if item["background"] not in ("beige", "brown"):
                fail(f"{page['news']} '{item['title']}': background 는 beige 또는 brown 이어야 합니다.")
            classes.append("bg-" + item["background"])
        body = "".join(f"<p>{format_citation(p).replace(chr(10), '<br>')}</p>" for p in item.get("body", []))
        items.append(f'        <article class="{" ".join(classes)}">{photo}<div class="news-text">'
                     f'<h3>{esc(item["date"])}: {esc(item["title"])}</h3>{body}</div></article>')
        text.append(f'{item["date"]}: {item["title"]} ' + " ".join(plain_text(p) for p in item.get("body", [])))
    body = join["body"] + '\n      <section class="news">\n        <h2 class="news-heading">NEWS</h2>\n' + "\n".join(items) + "\n      </section>"
    return {"body": body, "text": " ".join(text), "heading": page.get("heading", page["title"]),
            "banner_class": "banner banner-hero", "banner_extra": hero}


RENDERERS = {"publications": lambda page, site: render_publications(page),
             "people": render_people, "alumni": render_alumni, "hub": render_hub,
             "awards": render_awards, "html": render_html, "home": render_home}


# ── 공통 틀 ───────────────────────────────────────────────

def chevron():
    return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M16.59 8.59 12 13.17 7.41 8.59 6 10l6 6 6-6z"/></svg>'


def render_nav(menu, current):
    lines = []
    for entry in menu:
        children = entry.get("children", [])
        here = ' aria-current="page"' if entry["url"] == current else ""
        link = f'<a href="{entry["url"]}"{here}>{html.escape(entry["title"])}</a>'
        if not children:
            lines.append(f'      <div class="nav-item">{link}</div>')
            continue
        is_open = entry["url"] == current or any(c["url"] == current for c in children)
        # 상위 메뉴를 누르면 첫 번째 하위 페이지로 바로 이동 (예: RESEARCH → Reactor Design)
        link = f'<a href="{children[0]["url"]}"{here}>{html.escape(entry["title"])}</a>'
        sub = "".join(
            f'<a href="{c["url"]}"' + (' aria-current="page"' if c["url"] == current else "")
            + f'>{html.escape(c["title"])}</a>'
            for c in children
        )
        lines.append(
            f'      <div class="nav-item nav-group">'
            f'<button type="button" class="nav-toggle" aria-expanded="{str(is_open).lower()}" '
            f'aria-label="{html.escape(entry["title"])} submenu">{chevron()}</button>{link}'
            f'<div class="nav-children"{"" if is_open else " hidden"}>{sub}</div></div>'
        )
    return "\n".join(lines)


def with_base(document):
    """href="/..." · src="/..." · url('/...') 앞에 기준 경로를 붙입니다."""
    if not BASE:
        return document
    document = re.sub(r'((?:href|src)=")/(?!/)', rf"\g<1>{BASE}/", document)
    return document.replace("url('/", f"url('{BASE}/")


def main():
    site = tomllib.loads((DATA / "site.toml").read_text(encoding="utf-8"))
    template = Template((ROOT / "templates" / "base.html").read_text(encoding="utf-8"))

    # dist 폴더 자체는 두고 내용만 지웁니다(미리보기 서버가 켜져 있어도 동작하도록).
    DIST.mkdir(exist_ok=True)
    try:
        for item in DIST.iterdir():
            clear_readonly(item)
            shutil.rmtree(item, onexc=retry_writable) if item.is_dir() else item.unlink()
    except PermissionError as error:
        fail(f"dist 폴더의 파일을 지울 수 없습니다({error.filename}).\n"
             "탐색기나 다른 프로그램에서 dist 안의 파일·폴더를 열어 두었다면 닫고 다시 실행해 주세요.")
    shutil.copytree(ROOT / "static", DIST / "static", dirs_exist_ok=True)

    index_path = DIST / "search-index.json"
    search_index = []

    for page in site.get("page", []):
        render = RENDERERS.get(page["type"])
        if not render:
            fail(f"알 수 없는 페이지 종류입니다: {page['type']}")
        result = render(page, site)
        text = result["text"]
        document = template.substitute(
            title=html.escape(page["title"]),
            site_name=html.escape(site["name"]),
            description=html.escape(site["description"]),
            logo=site["logo"],
            banner=page["banner"] if isinstance(page.get("banner"), str) else site["banner"],
            banner_class=result.get("banner_class", "banner"),
            banner_extra=result.get("banner_extra", ""),
            heading=html.escape(result.get("heading", page["title"])),
            nav=render_nav(site["menu"], page["url"]),
            body=result["body"],
            base=BASE,
        )
        document = with_base(document)
        target = DIST / page["output"] if page.get("output") else DIST / page["url"].strip("/") / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(document, encoding="utf-8")
        if page["url"] == site.get("home", "/main"):
            (DIST / "index.html").write_text(document, encoding="utf-8")  # 도메인 첫 화면(/)도 메인으로

        if not page.get("output"):  # 404 같은 특수 페이지는 검색에서 제외
            search_index.append({"route": page["url"], "title": page["title"], "text": text})
        print(f"  {page['url']}")

    index_path.write_text(json.dumps(search_index, ensure_ascii=False), encoding="utf-8")
    print(f"완료 → {DIST}")


if __name__ == "__main__":
    main()
