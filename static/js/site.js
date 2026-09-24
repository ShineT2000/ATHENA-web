// ATHENA 웹사이트 동작: 메뉴, 모바일 메뉴, 검색, 주소(#연도)로 연도 목록 열기

// 사이트가 하위 경로(예: GitHub Pages 의 /ATHENA-website)에 있을 때의 기준 경로
const BASE = document.documentElement.dataset.base || "";

// 하위 메뉴 펼치기/접기
document.querySelectorAll(".nav-toggle").forEach((button) => {
  button.addEventListener("click", () => {
    const open = button.getAttribute("aria-expanded") !== "true";
    button.setAttribute("aria-expanded", String(open));
    button.parentElement.querySelector(".nav-children").hidden = !open;
  });
});

// 모바일 메뉴
const menuButton = document.querySelector(".menu-button");
const setMenu = (open) => {
  document.body.classList.toggle("nav-open", open);
  menuButton.setAttribute("aria-expanded", String(open));
  menuButton.setAttribute("aria-label", open ? "Close navigation" : "Open navigation");
};
menuButton.addEventListener("click", () => setMenu(!document.body.classList.contains("nav-open")));
document.querySelector("main").addEventListener("click", () => setMenu(false));
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") setMenu(false);
});

// 주소에 #y2015 처럼 연도가 있으면 해당 목록을 열고 이동
const openFromHash = () => {
  const target = location.hash && document.getElementById(decodeURIComponent(location.hash.slice(1)));
  const details = target && target.closest("details");
  if (details) {
    details.open = true;
    target.scrollIntoView();
  }
};
window.addEventListener("hashchange", openFromHash);
openFromHash();

// 사이트 검색
const dialog = document.querySelector(".search-dialog");
const input = document.querySelector("#search-input");
const results = document.querySelector(".search-results");
let index;

document.querySelector(".search-button").addEventListener("click", async () => {
  dialog.showModal();
  input.focus();
  if (index) return;
  try {
    const response = await fetch(BASE + "/search-index.json");
    if (!response.ok) throw new Error(response.statusText);
    index = await response.json();
  } catch {
    results.textContent = "Search is currently unavailable. Please use the navigation menu.";
  }
});

dialog.addEventListener("click", (event) => {
  // 바깥(어두운 부분) 클릭 시 닫기. 창 안쪽 여백 클릭도 target이 dialog이므로 좌표로 구분합니다.
  const box = dialog.getBoundingClientRect();
  const outside = event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom;
  if (event.target === dialog && outside) dialog.close();
});

input.addEventListener("input", () => {
  results.replaceChildren();
  const query = input.value.trim().toLowerCase();
  if (!query || !index) return;
  const matches = index.filter((page) => (page.title + " " + page.text).toLowerCase().includes(query));
  if (!matches.length) {
    results.textContent = "No results found.";
    return;
  }
  for (const page of matches) {
    const link = document.createElement("a");
    link.className = "search-result";
    link.href = BASE + page.route;
    const title = document.createElement("strong");
    title.textContent = page.title;
    const excerpt = document.createElement("p");
    const start = Math.max(0, page.text.toLowerCase().indexOf(query) - 60);
    excerpt.textContent = (start > 0 ? "…" : "") + page.text.slice(start, start + 220) + "…";
    link.append(title, excerpt);
    results.append(link);
  }
});

// 이미지 슬라이드 (.carousel 안의 사진들): 이전/다음 버튼, 점, 키보드 ←/→
const arrow = (d) => `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${d}"/></svg>`;
document.querySelectorAll(".carousel").forEach((carousel) => {
  const slides = [...carousel.querySelectorAll(":scope > img")];
  if (slides.length < 2) return;
  let current = 0;
  const dots = document.createElement("div");
  dots.className = "carousel-dots";
  const show = (index) => {
    current = (index + slides.length) % slides.length;
    slides.forEach((img, i) => img.classList.toggle("active", i === current));
    [...dots.children].forEach((dot, i) => dot.setAttribute("aria-current", String(i === current)));
  };
  slides.forEach((img, i) => {
    const dot = document.createElement("button");
    dot.type = "button";
    dot.setAttribute("aria-label", `Image ${i + 1} of ${slides.length}`);
    dot.addEventListener("click", () => show(i));
    dots.append(dot);
  });
  const button = (cls, label, path, step) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = `carousel-button ${cls}`;
    b.setAttribute("aria-label", label);
    b.innerHTML = arrow(path);
    b.addEventListener("click", () => show(current + step));
    return b;
  };
  carousel.append(
    button("prev", "Previous image", "M15.41 16.59 10.83 12l4.58-4.59L14 6l-6 6 6 6z", -1),
    button("next", "Next image", "M8.59 16.59 13.17 12 8.59 7.41 10 6l6 6-6 6z", 1),
    dots,
  );
  carousel.tabIndex = 0;
  carousel.setAttribute("aria-roledescription", "carousel");
  carousel.addEventListener("keydown", (event) => {
    if (event.key === "ArrowLeft") show(current - 1);
    if (event.key === "ArrowRight") show(current + 1);
  });
  carousel.classList.add("ready");
  show(0);
});

// 메인 첫 화면의 아래 화살표
document.querySelector(".scroll-down")?.addEventListener("click", () => {
  document.querySelector(".page-body").scrollIntoView({ behavior: "smooth" });
});
