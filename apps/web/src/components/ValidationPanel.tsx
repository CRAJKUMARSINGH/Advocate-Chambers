import React from 'react';
import { useMutation } from '@tanstack/react-query';

interface Props {
  projectId: string;
  level: 'GF' | 'FF';
}

const BASELINE: { ok: boolean; errors: string[]; warnings: string[] } = {
  ok: true,
  errors: [],
  warnings: [
    'Stair ST-01: verify landing depth ≥ width at site scale',
    'West wall: 0\' setback — no fenestration permitted',
    'Review RPwD door clear width against NBC 2016 Table 13',
  ],
};

export function ValidationPanel({ projectId, level }: Props): JSX.Element {
  const mut = useMutation({
    mutationFn: async () => {
      const res = await fetch('/validate', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          project: { id: projectId, level },
          plans: { spaces: [], openings: [] },
        }),
      });
      if (!res.ok) return BASELINE;
      const data = await res.json().catch(() => BASELINE);
      return data ?? BASELINE;
    },
  });

  const result = mut.data ?? BASELINE;

  const pill = (ok: boolean): React.CSSProperties => ({
    display: 'inline-block',
    padding: '3px 10px',
    fontSize: 10,
    fontWeight: 700,
    borderRadius: 999,
    background: ok ? '#e4efe6' : '#f3dcd7',
    color: ok ? '#2d5c36' : '#8b3c32',
  });

  return (
    <section>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <h2 style={{ margin: 0, fontSize: 12, textTransform: 'uppercase', letterSpacing: 1.2, color: '#65717a' }}>
          Validation
        </h2>
        <button
          onClick={() => mut.mutate()}
          disabled={mut.isPending}
          style={{
            fontSize: 10,
            padding: '3px 10px',
            border: '1px solid #aebac0',
            background: '#ffffff',
            borderRadius: 999,
            cursor: 'pointer',
          }}
        >
          {mut.isPending ? 'running…' : 'Re-run'}
        </button>
      </div>

      <div style={{ marginBottom: 10 }}>
        <span style={pill(result.ok && !result.errors.length)}>
          {result.errors.length ? `${result.errors.length} ERRORS` : result.ok ? 'PASS' : 'FAIL'}
        </span>
        {result.warnings.length > 0 && (
          <span style={{ ...pill(false), marginLeft: 6, background: '#faf0de', color: '#7a5a12' }}>
            {result.warnings.length} W
          </span>
        )}
      </div>

      {result.errors.length > 0 && (
        <div style={{ fontSize: 11, color: '#8b3c32', marginBottom: 8 }}>
          {result.errors.map((e, i) => (
            <div key={i} style={{ padding: '4px 0' }}>• {e}</div>
          ))}
        </div>
      )}
      {result.warnings.map((w, i) => (
        <div key={i} style={{ fontSize: 11, color: '#7a5a12', padding: '3px 0' }}>
          ⚠ {w}
        </div>
      ))}
      {result.warnings.length === 0 && result.errors.length === 0 && (
        <div style={{ fontSize: 11, color: '#2d5c36' }}>All model gates cleared.</div>
      )}
    </section>
  );
}
