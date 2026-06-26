// Real-world high-fidelity technical features from our prompt evaluation dataset
// Used to make demo walkthrough recordings look completely authentic and professional.

export const demoFeatures = {
  anchorPositioning: {
    name: "CSS Anchor Positioning",
    category: "CSS",
    summary: "Allows positioning a positioned element relative to one or more other anchor elements on the page. This eliminates the need for complex JavaScript calculations for popup positioning and tooltips, enabling high-performance visual alignments.",
    explainer: "https://github.com/w3c/csswg-drafts/issues/8927",
    spec: "https://drafts.csswg.org/css-anchor-position-1/"
  },
  popover: {
    name: "Popover API",
    category: "HTML",
    summary: "Provides a standard, browser-native mechanism for displaying transient content on top of other page content. This includes tooltips, menus, and teaching UI, managing z-index stack and light-dismiss behaviors natively.",
    explainer: "https://github.com/whatwg/html/pull/8230",
    spec: "https://html.spec.whatwg.org/multipage/popover.html"
  },
  cssPaint: {
    name: "CSS Painting API",
    category: "CSS",
    summary: "Allows developers to write JavaScript functions that can draw directly into an element's background, border, or content via the CSS paint() function, enabling high-performance custom visual effects.",
    explainer: "https://github.com/w3c/css-houdini-drafts/tree/main/css-paint-api",
    spec: "https://drafts.css-houdini.org/css-paint-api-1/"
  }
};
