import React from 'react';
import { useMutation } from '@tanstack/react-query';

interface Props {
  projectId: string;
  level: 'GF' | 'FF';
  selectedId: string | null;
}

const SAMPLE_SELECTION: Record<string, { kind: string; props: [string, string][] }> = {
  'GF-01': { kind: 'space (assembly lobby)', props: [['Size', "30' × 8'"], ['Finish', 'public'], ['D-tag', 'D-MAIN 2×4-0']] },
  'GF-02': { kind: 'space (private office)', props: [['Size', "15' × 8.5'"], ['Finish', 'service'], ['D-tag', 'D-GF-02 3-0']] },
  'GF-03': { kind: 'space (service)', props: [['Size', "15' × 8.5'"], ['Fixtures M', '5 urinals · 2 WCs'], ['Fixtures F', '3 WCs']] },
  'GF-04': { kind: 'space (assembly hall)', props: [['Size', "46' × 44.5'"], ['Finish', 'public'], ['Seating', 'chairs only — no tables']] },
  'GF-05': { kind: 'space (chamber)', props: [['Size', "16' × 12'"], ['Attached WC', '9\' × 6\' (54 sft)'], ['Area total', '246 sft']] },
  'GF-06': { kind: 'space (chamber)', props: [['Size', "15' × 12'"], ['Attached WC', '9\' × 6\' (54 sft)'], ['Area total', '234 sft']] },
  'GF-STAIR': { kind: 'stair (dog-leg 180°)', props: [['Compartment', "9'-0\" W × 33'-0\" L"], ['Risers', '2×13 = 26 @ 6.85"'], ['Treads', '12" with 1.5" nosing']] },
};

export function PropertyInspector({ projectId, level, selectedId }: Props): JSX.Element {
  const empty = !selectedId;

  const info = selectedId ? SAMPLE_SELECTION[selectedId] : undefined;
  const mutate = useMutation({
    mutationFn: async () => {
      const res = await fetch('/health', { method: 'GET' });
      return res.json();
    },
  });

  return (
    <section style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <h2 style={{ margin: 0, fontSize: 12, textTransform: 'uppercase', letterSpacing: 1.2, color: '#65717a' }}>
        Property Inspector
      </h2>

      <div
        style={{
          padding: 12,
          border: '1px dashed #c7d0d4',
          borderRadius: 6,
          background: '#f6f8f8',
          fontSize: 12,
          color: empty ? '#65717a' : '#192530',
        }}
      >
        {empty ? (
          <>Click a space in the viewport to review its parameters.</>
        ) : (
          <>
            <div style={{ fontSize: 11, color: '#65717a', marginBottom: 4 }}>
              <code>{selectedId}</code> · {info?.kind ?? 'object'}
            </div>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <tbody>
                {(info?.props ?? []).map(([k, v]) => (
                  <tr key={k}>
                    <td style={{ padding: '4px 0', color: '#65717a', width: '42%' }}>{k}</td>
                    <td style={{ padding: '4px 0', fontWeight: 600 }}>{v}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </div>

      <div style={{ fontSize: 11, color: '#65717a', marginTop: 4 }}>
        <div style={{ marginBottom: 6, fontWeight: 600 }}>Editor policy (Patch 3)</div>
        <ul style={{ margin: 0, paddingLeft: 18 }}>
          <li>The browser proposes edits.</li>
          <li>Python validates and persists accepted revisions.</li>
          <li>DXF/PDF are generated on the server only.</li>
        </ul>
      </div>

      <button
        onClick={() => mutate.mutate()}
        disabled={mutate.isPending}
        style={{
          marginTop: 'auto',
          padding: '10px 12px',
          border: '1px solid #2e5c62',
          background: '#ffffff',
          color: '#2e5c62',
          borderRadius: 6,
          fontWeight: 700,
          cursor: mutate.isPending ? 'wait' : 'pointer',
          fontSize: 12,
        }}
      >
        {mutate.isPending
          ? 'Ping API…'
          : mutate.data
            ? `API online · rev ${mutate.data.version}`
            : `Ping FastAPI /health (${projectId} · ${level})`}
      </button>
    </section>
  );
}
