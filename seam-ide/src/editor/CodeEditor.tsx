import { useEffect, useRef, useState } from 'react';
import { EditorState } from '@codemirror/state';
import { EditorView, keymap, lineNumbers, highlightActiveLine, drawSelection } from '@codemirror/view';
import { defaultKeymap, history, historyKeymap } from '@codemirror/commands';
import { searchKeymap, highlightSelectionMatches } from '@codemirror/search';
import { foldGutter, indentOnInput, syntaxHighlighting, defaultHighlightStyle } from '@codemirror/language';
import { languageForPath } from './languages';
import { EditorMinimap } from '../components/EditorMinimap';

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
  const [scrollInfo, setScrollInfo] = useState({ scrollTop: 0, scrollHeight: 1, clientHeight: 1 });

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
    const view = new EditorView({ state, parent: hostRef.current });
    viewRef.current = view;

    const scrollDOM = view.scrollDOM;
    const updateScroll = () => {
      setScrollInfo({
        scrollTop: scrollDOM.scrollTop,
        scrollHeight: scrollDOM.scrollHeight,
        clientHeight: scrollDOM.clientHeight,
      });
    };
    updateScroll();
    scrollDOM.addEventListener('scroll', updateScroll, { passive: true });

    return () => {
      scrollDOM.removeEventListener('scroll', updateScroll);
      view.destroy();
    };
  }, [path, version, wordWrap]);

  return (
    <div className="codeEditorWrapper">
      <div className="editorHost" ref={hostRef} />
      <EditorMinimap
        content={content}
        scrollTop={scrollInfo.scrollTop}
        scrollHeight={scrollInfo.scrollHeight}
        clientHeight={scrollInfo.clientHeight}
        onScrollTo={(pos) => {
          if (viewRef.current) {
            viewRef.current.scrollDOM.scrollTop = pos;
          }
        }}
      />
    </div>
  );
}
