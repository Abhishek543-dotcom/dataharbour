export default function CellOutput({ outputs }) {
  if (!outputs || outputs.length === 0) {
    return null;
  }

  return (
    <div className="border-t border-slate-200 bg-slate-50">
      {outputs.map((output, index) => (
        <div key={index} className="px-4 py-3">
          {output.output_type === 'stream' && (
            <pre className="text-sm text-slate-700 font-mono whitespace-pre-wrap">
              {output.text}
            </pre>
          )}

          {output.output_type === 'execute_result' && (
            <pre className="text-sm text-slate-700 font-mono whitespace-pre-wrap">
              {output.data?.['text/plain'] || JSON.stringify(output.data, null, 2)}
            </pre>
          )}

          {output.output_type === 'error' && (
            <div className="bg-red-50 border border-red-200 rounded p-3">
              <div className="text-sm font-semibold text-red-800 mb-1">
                {output.ename}: {output.evalue}
              </div>
              <pre className="text-xs text-red-700 font-mono whitespace-pre-wrap">
                {output.traceback?.join('\n')}
              </pre>
            </div>
          )}

          {output.output_type === 'display_data' && output.data?.['text/plain'] && (
            <pre className="text-sm text-slate-700 font-mono whitespace-pre-wrap">
              {output.data['text/plain']}
            </pre>
          )}
        </div>
      ))}
    </div>
  );
}
