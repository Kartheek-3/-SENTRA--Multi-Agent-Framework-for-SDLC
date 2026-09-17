import { StreamLanguage } from '@codemirror/language';
import { python } from '@codemirror/lang-python';
import { javascript } from '@codemirror/lang-javascript';
import { json } from '@codemirror/lang-json';
import { markdown } from '@codemirror/lang-markdown';
import { html } from '@codemirror/lang-html';
import { css } from '@codemirror/lang-css';
import { sql } from '@codemirror/lang-sql';

export function languageForPath(path: string) {
  const lower = path.toLowerCase();
  if (lower.endsWith('.py')) return python();
  if (lower.endsWith('.ts') || lower.endsWith('.tsx')) return javascript({ typescript: true, jsx: lower.endsWith('.tsx') });
  if (lower.endsWith('.js') || lower.endsWith('.jsx')) return javascript({ jsx: lower.endsWith('.jsx') });
  if (lower.endsWith('.json')) return json();
  if (lower.endsWith('.md')) return markdown();
  if (lower.endsWith('.html')) return html();
  if (lower.endsWith('.css')) return css();
  if (lower.endsWith('.sql')) return sql();
  if (lower.endsWith('.yaml') || lower.endsWith('.yml')) return StreamLanguage.define({
    token(stream) {
      if (stream.match(/#.*/)) return 'comment';
      if (stream.match(/".*?"/) || stream.match(/'.*?'/)) return 'string';
      if (stream.match(/[A-Za-z0-9_-]+:/)) return 'keyword';
      stream.next();
      return null;
    },
  });
  return [];
}
