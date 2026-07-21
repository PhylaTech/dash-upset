/**
 * Tabbed install widget. Wires any element with [data-install]: clicking a
 * .install-tab shows the matching .install-panel.
 */
(function () {
    "use strict";

    function wire(root) {
        var widgets = root.querySelectorAll("[data-install]");
        Array.prototype.forEach.call(widgets, function (w) {
            // Scope to THIS widget's own tabs/panels so nested [data-install]
            // widgets (e.g. constructors inside a quick-start tab) don't get
            // toggled by their parent.
            var scoped = function (sel) {
                return Array.prototype.filter.call(w.querySelectorAll(sel), function (n) {
                    return n.closest("[data-install]") === w;
                });
            };
            var tabs = scoped(".install-tab");
            var panels = scoped(".install-panel");
            Array.prototype.forEach.call(tabs, function (tab) {
                tab.addEventListener("click", function () {
                    var target = tab.getAttribute("data-target");
                    Array.prototype.forEach.call(tabs, function (t) {
                        t.classList.toggle("is-active", t === tab);
                        t.setAttribute("aria-selected", t === tab ? "true" : "false");
                    });
                    Array.prototype.forEach.call(panels, function (p) {
                        p.classList.toggle("is-active", p.getAttribute("data-panel") === target);
                    });
                });
            });
        });
    }

    if (document.readyState !== "loading") {
        wire(document);
    } else {
        document.addEventListener("DOMContentLoaded", function () { wire(document); });
    }
})();
