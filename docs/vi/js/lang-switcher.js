(function () {
  function normalizeIndex(path) {
    return path.replace(/\/index\.html\/?$/, "/index.html");
  }

  function currentLang(pathname) {
    return pathname.startsWith("/en/") ? "en" : "vi";
  }

  function targetPath(pathname, targetLang) {
    var path = normalizeIndex(pathname);
    if (targetLang === "en") {
      return path.startsWith("/en/") ? path : "/en" + path;
    }
    return path.startsWith("/en/") ? path.slice(3) : path;
  }

  function translateHeader(lang) {
    var translations = {
      "View on Github": "Xem trên GitHub",
      "Edit on GitHub": "Sửa trên GitHub",
    };

    var items = document.querySelectorAll("cds-header-nav-item");
    items.forEach(function (item) {
      var text = (item.textContent || "").trim();
      if (!text) return;
      if (lang === "vi" && translations[text]) {
        item.textContent = translations[text];
      } else if (lang === "en") {
        var reverse = Object.keys(translations).find(function (key) {
          return translations[key] === text;
        });
        if (reverse) item.textContent = reverse;
      }
    });

    var label = document.querySelector(".lang-switcher__label");
    if (label) label.textContent = lang === "en" ? "Language" : "Ngôn ngữ";
  }

  function insertSwitcher() {
    var header = document.querySelector("cds-header");
    if (!header) return;

    var container = document.createElement("div");
    container.className = "lang-switcher";
    container.setAttribute("role", "group");
    container.setAttribute("aria-label", "Language switcher");

    var label = document.createElement("span");
    label.className = "lang-switcher__label";
    label.textContent = "Ngôn ngữ";

    var select = document.createElement("select");
    select.className = "lang-switcher__select";
    select.setAttribute("aria-label", "Language");

    var optVi = document.createElement("option");
    optVi.value = "vi";
    optVi.textContent = "VI";
    var optEn = document.createElement("option");
    optEn.value = "en";
    optEn.textContent = "EN";

    select.appendChild(optVi);
    select.appendChild(optEn);
    container.appendChild(label);
    container.appendChild(select);

    var nav = header.querySelector("cds-header-nav");
    if (nav) {
      header.insertBefore(container, nav);
    } else {
      header.appendChild(container);
    }

    var lang = currentLang(window.location.pathname || "/");
    select.value = lang;
    translateHeader(lang);

    select.addEventListener("change", function () {
      var next = targetPath(window.location.pathname || "/", select.value);
      window.location.href = next + window.location.search + window.location.hash;
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", insertSwitcher);
  } else {
    insertSwitcher();
  }
})();
