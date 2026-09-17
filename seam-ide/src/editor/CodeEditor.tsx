import { useEffect, useRef } from 'react';
import { EditorState } from '@codemirror/state';
import { EditorView, keymap, lineNumbers, highlightActiveLine, drawSelection } from '@codemirror/view';
import { defaultKeymap, history, historyKeymap } from '@codemirror/commands';
import { searchKeymap, highlightSelectionMatches } from '@codemirror/search';
import { foldGutter, indentOnInput, syntaxHighlighting, defaultHighlightStyle } from '@codemirror/language';
import { languageForPath } from './languages';

type Props = {
  path: string;
  content: string;
  version: number;
  wordWrap: boolean;
  onChange: (content: string) => void;
};

export function CodeEditor({ path, content, version, wordWrap, onChange }: Props) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const viewRef = useRef<EditorView | null>(null);
  const onChangeRef = useRef(onChange);

  useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);

  useEffect(() => {
    if (!hostRef.current) return;
    viewRef.current?.destroy();
    const state = EditorState.create({
      doc: content,
      extensions: [
        lineNumbers(),
        foldGutter(),
        history(),
        drawSelection(),
        highlightActiveLine(),
        highlightSelectionMatches(),
        indentOnInput(),
        syntaxHighlighting(defaultHighlightStyle),
        keymap.of([...defaultKeymap, ...historyKeymap, ...searchKeymap]),
        languageForPath(path),
        wordWrap ? EditorView.lineWrapping : [],
        EditorView.updateListener.of(update => {
          if (update.docChanged) onChangeRef.current(update.state.doc.toString());
        }),
      ],
    });
    viewRef.current = new EditorView({ state, parent: hostRef.current });
    return () => viewRef.current?.destroy();
  }, [path, version, wordWrap]);

  return <div className="editorHost" ref={hostRef} />;
}
