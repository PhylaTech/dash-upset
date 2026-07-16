/**
 * Shared site navigation, matched to the dash-seqviz house style.
 * Renders a sticky top bar into any element with id="site-nav-mount".
 * The active link is chosen from <body data-page="home|examples|docs">.
 */
(function () {
    var REPO = "https://github.com/PhylaTech/dash-upset";
    var LINKS = [
        { id: "home", label: "Home", href: "./" },
        { id: "examples", label: "Examples", href: "./examples.html" },
        { id: "docs", label: "Docs", href: REPO + "#readme", external: true },
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
        brand.innerHTML = 'dash-<span>upset</span>';
        inner.appendChild(brand);

        var links = document.createElement("div");
        links.className = "site-nav-links";
        LINKS.forEach(function (link) {
            var a = document.createElement("a");
            a.href = link.href;
            a.textContent = link.label;
            if (link.external) { a.target = "_blank"; a.rel = "noopener"; }
            if (link.id === page) a.className = "active";
            links.appendChild(a);
        });
        inner.appendChild(links);

        var gh = document.createElement("a");
        gh.className = "site-nav-github";
        gh.href = REPO;
        gh.target = "_blank";
        gh.rel = "noopener";
        gh.textContent = "GitHub";
        inner.appendChild(gh);

        nav.appendChild(inner);
        mount.replaceWith(nav);
    }

    function wireCopy(root) {
        (root || document).querySelectorAll(".snippet").forEach(function (snip) {
            if (snip.querySelector(".snippet-copy")) return;
            var pre = snip.querySelector("pre");
            if (!pre) return;
            var btn = document.createElement("button");
            btn.className = "snippet-copy";
            btn.textContent = "Copy";
            btn.addEventListener("click", function () {
                navigator.clipboard.writeText(pre.innerText).then(function () {
                    btn.textContent = "Copied";
                    btn.classList.add("copied");
                    setTimeout(function () {
                        btn.textContent = "Copy";
                        btn.classList.remove("copied");
                    }, 1500);
                });
            });
            snip.appendChild(btn);
        });
    }

    window.DashUpsetSite = { wireCopy: wireCopy };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function () {
            renderNav();
            wireCopy(document);
        });
    } else {
        renderNav();
        wireCopy(document);
    }
})();
