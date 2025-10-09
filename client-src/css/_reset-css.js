import {css} from 'lit';

export const RESET = css`
html, body {
  margin: 0;
  padding: 0;
  border: 0;
  font-weight: inherit;
  font-style: inherit;
  font-size: 100%;
  font-family: inherit;
  vertical-align: baseline;
}

div, span, object, iframe, h1, h2, h3, h4, h5, h6, p,
pre, a, abbr, acronym, address, code, del, dfn, em, img,
dl, dt, dd, ol, ul, li, fieldset, form, label, legend, caption, tbody, tfoot, thead, tr {
  margin: 0;
  padding: 0;
  border: 0;
  font-weight: inherit;
  font-size: 100%;
  font-family: inherit;
  vertical-align: baseline;
}

ol, ul {
  padding: revert;
}

blockquote, q {
  margin: 0;
  padding: 0;
  border: 0;
  font-weight: inherit;
  font-style: inherit;
  font-size: 100%;
  font-family: inherit;
  vertical-align: baseline;
  quotes: "" "";
}

blockquote {
  margin-left: 1em;
  border-left: 2px solid #999;
  padding-left: 1em;
}

blockquote:before, q:before,
blockquote:after, q:after {
  content: "";
}

th, td, caption {
  margin: 0;
  padding: 0;
  border: 0;
  font-weight: inherit;
  font-style: inherit;
  font-size: 100%;
  font-family: inherit;
  vertical-align: baseline;
  text-align: left;
  font-weight: normal;
  vertical-align: middle;
}

table {
  margin: 0;
  padding: 0;
  border: 0;
  font-weight: inherit;
  font-style: inherit;
  font-size: 100%;
  font-family: inherit;
  vertical-align: baseline;
  border-collapse: separate;
  border-spacing: 0;
  vertical-align: middle;
}

a img {
  border: none;
}
`;
