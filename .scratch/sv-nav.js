/**
 * Shared site navigation.
 * Renders a sticky top bar into any element with id="site-nav-mount".
 * The active link is determined from
 * <body data-page="home|explorer|integrations|reference">.
 */
(function () {
    var LINKS = [
        { id: "home",         label: "Home",               href: "./" },
        { id: "explorer",     label: "Component Explorer", href: "./explorer.html" },
        { id: "integrations", label: "Integrations",       href: "./integrations.html" },
        { id: "reference",    label: "Reference",          href: "./reference.html" }
    ];

    function renderNav() {
        var mount = document.getElementById("site-nav-mount");
        if (!mount) return;

        var page = (document.body && document.body.getAttribute("data-page")) || "";

        var nav = document.createElement("nav");
        nav.className = "site-nav";

        var inner = document.createElement("div");
        inner.className = "site-nav-inner";

        var brand = document.createElement("a");
        brand.className = "site-nav-brand";
        brand.href = "./";
        brand.innerHTML = '<img class="site-nav-logo" src="./assets/logo-mark.svg" alt="" width="22" height="22" aria-hidden="true"><span class="site-nav-wordmark">dash-<span>seqviz</span></span>';
        inner.appendChild(brand);

        var links = document.createElement("div");
        links.className = "site-nav-links";
        LINKS.forEach(function (link) {
            var a = document.createElement("a");
            a.href = link.href;
            a.textContent = link.label;
            if (link.external) {
                a.target = "_blank";
                a.rel = "noopener";
            }
            if (link.id === page) a.className = "active";
            links.appendChild(a);
        });
        inner.appendChild(links);

        var gh = document.createElement("a");
        gh.className = "site-nav-github";
        gh.href = "https://github.com/Full-Spectrum-Analytics/dash-seqviz";
        gh.target = "_blank";
        gh.rel = "noopener";
        gh.textContent = "GitHub";
        inner.appendChild(gh);

        nav.appendChild(inner);
        mount.replaceWith(nav);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", renderNav);
    } else {
        renderNav();
    }
})();
