import { useState } from 'react';
import CodeMirror from '@uiw/react-codemirror';
import { python } from '@codemirror/lang-python';
import { Play, Trash2, ChevronUp, ChevronDown } from 'lucide-react';
import Button from '../ui/Button';
import CellOutput from './CellOutput';

export default function NotebookCell({ cell, onExecute, onDelete, onMove, isFirst, isLast, executing }) {
  const [code, setCode] = useState(cell.source || '');

  const handleExecute = () => {
    onExecute(cell.id, code);
  };

  return (
    <div className="border border-slate-200 rounded-lg overflow-hidden bg-white mb-4">
      {/* Cell Toolbar */}
      <div className="flex items-center justify-between px-3 py-2 bg-slate-50 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-slate-500">
            {cell.cell_type === 'code' ? 'Code' : 'Markdown'}
          </span>
          {cell.execution_count && (
            <span className="text-xs text-slate-400">
              [{cell.execution_count}]
            </span>
          )}
        </div>

        <div className="flex items-center gap-1">
          {cell.cell_type === 'code' && (
            <Button
              size="sm"
              variant="ghost"
              onClick={handleExecute}
              disabled={executing}
            >
              <Play className="w-4 h-4 mr-1" />
              {executing ? 'Running...' : 'Run'}
            </Button>
          )}

          <Button
            size="sm"
            variant="ghost"
            onClick={() => onMove(cell.id, 'up')}
            disabled={isFirst}
          >
            <ChevronUp className="w-4 h-4" />
          </Button>

          <Button
            size="sm"
            variant="ghost"
            onClick={() => onMove(cell.id, 'down')}
            disabled={isLast}
          >
            <ChevronDown className="w-4 h-4" />
          </Button>

          <Button
            size="sm"
            variant="ghost"
            onClick={() => onDelete(cell.id)}
            className="text-red-600 hover:text-red-700"
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Cell Editor */}
      <div className="relative">
        <CodeMirror
          value={code}
          height="auto"
          minHeight="60px"
          extensions={[python()]}
          onChange={(value) => setCode(value)}
          theme="light"
          basicSetup={{
            lineNumbers: true,
            highlightActiveLineGutter: true,
            highlightSpecialChars: true,
            foldGutter: true,
            drawSelection: true,
            dropCursor: true,
            allowMultipleSelections: true,
            indentOnInput: true,
            syntaxHighlighting: true,
            bracketMatching: true,
            closeBrackets: true,
            autocompletion: true,
            rectangularSelection: true,
            crosshairCursor: true,
            highlightActiveLine: true,
            highlightSelectionMatches: true,
            closeBracketsKeymap: true,
            searchKeymap: true,
            foldKeymap: true,
            completionKeymap: true,
            lintKeymap: true,
          }}
        />
      </div>

      {/* Cell Output */}
      {cell.outputs && cell.outputs.length > 0 && (
        <CellOutput outputs={cell.outputs} />
      )}
    </div>
  );
}
