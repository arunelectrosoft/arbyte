/*!
 * mermaid-runtime.js
 *
 * Client-side runtime that renders <div class="mermaid"> diagrams inline
 * and adapts the rendered layout to the current viewport (mobile, tablet,
 * web browser / desktop, and large TV/display screens).
 *
 * Why not just `mermaid.initialize({ startOnLoad: true })`?
 * Mermaid replaces a `.mermaid` element's text content with the rendered
 * SVG the first time it runs, so the original diagram source is lost and
 * can't be re-rendered later. This runtime keeps a copy of each diagram's
 * source and re-renders it whenever the viewport crosses a breakpoint,
 * enforcing a compact top-down flow on every screen size so diagrams remain
 * contained by cards rather than becoming long horizontal strips.
 *
 * Requires mermaid.min.js to be loaded first, and
 * `mermaid.initialize({ startOnLoad: false, ... })` to be called before
 * this script runs (see _includes/footer.html).
 */
(function () {
  "use strict";

  if (typeof window === "undefined" || typeof window.mermaid === "undefined") {
    return;
  }

  // Diagram files are repository content, but strict mode remains essential:
  // it sanitizes labels and disables Mermaid JavaScript callback directives.
  window.mermaid.initialize({
    startOnLoad: false,
    theme: "default",
    securityLevel: "strict",
    flowchart: { useMaxWidth: true, htmlLabels: false },
    sequence: { useMaxWidth: true },
    gantt: { useMaxWidth: true },
  });

  // Breakpoints (px) matching assets/custom/_mermaid.scss.
  var BREAKPOINTS = {
    mobile: 0,
    tablet: 768,
    desktop: 992,
    tv: 1400,
  };

  function currentBreakpoint() {
    var width = window.innerWidth || document.documentElement.clientWidth;
    if (width >= BREAKPOINTS.tv) return "tv";
    if (width >= BREAKPOINTS.desktop) return "desktop";
    if (width >= BREAKPOINTS.tablet) return "tablet";
    return "mobile";
  }

  // Keep every flowchart vertical. The cards deliberately have bounded width;
  // switching desktop diagrams back to LR would overflow those card bounds.
  var DIRECTION_BY_BREAKPOINT = {
    mobile: "TD",
    tablet: "TD",
    desktop: "TD",
    tv: "TD",
  };

  var DIRECTIVE_RE = /^\s*(graph|flowchart)\s+(TD|TB|BT|RL|LR)\b/i;

  function adaptSourceToBreakpoint(source, breakpoint) {
    var direction = DIRECTION_BY_BREAKPOINT[breakpoint];
    if (!direction) return source;
    return source.replace(DIRECTIVE_RE, function (_match, keyword) {
      return keyword + " " + direction;
    });
  }

  var renderCounter = 0;

  function renderDiagram(container, breakpoint) {
    var source = container.getAttribute("data-mermaid-source");
    if (!source) return;

    var adapted = adaptSourceToBreakpoint(source, breakpoint);
    var renderId = "mermaid-runtime-" + Date.now() + "-" + renderCounter++;

    window.mermaid
      .render(renderId, adapted)
      .then(function (result) {
        container.innerHTML = result.svg;
        if (typeof result.bindFunctions === "function") {
          result.bindFunctions(container);
        }
        container.setAttribute("data-mermaid-breakpoint", breakpoint);
      })
      .catch(function (error) {
        console.error("mermaid-runtime: failed to render diagram", error);
      });
  }

  function renderAll(force) {
    var breakpoint = currentBreakpoint();
    var containers = document.querySelectorAll(".mermaid");

    containers.forEach(function (container) {
      if (!container.hasAttribute("data-mermaid-source")) {
        // First run: the element's text content is still the raw diagram
        // source (mermaid hasn't touched it yet), so capture it once.
        container.setAttribute("data-mermaid-source", container.textContent.trim());
      }
      if (!force && container.getAttribute("data-mermaid-breakpoint") === breakpoint) {
        return; // Already rendered for this breakpoint; nothing to do.
      }
      renderDiagram(container, breakpoint);
    });
  }

  function debounce(fn, delayMs) {
    var timeoutId;
    return function () {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(fn, delayMs);
    };
  }

  document.addEventListener("DOMContentLoaded", function () {
    renderAll(true);
  });

  window.addEventListener(
    "resize",
    debounce(function () {
      renderAll(false);
    }, 200)
  );
})();
