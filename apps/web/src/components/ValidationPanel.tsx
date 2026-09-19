import React from 'react';
import { useQuery } from '@tanstack/react-query';

interface Props {
  projectId: string;
  level: 'GF' | 'FF';
}

type Finding = {
  id: string;
  severity: string;
  rule: string;
  message: string;
  suggestedFixes: string[];
};

type Analysis = {
  status: string;
  findingCounts: Record<string, number>;
  findings: Finding[];
};

export function ValidationPanel({ projectId, level }: Props): React.JSX.Element {
  const query = useQuery<Analysis>({
    queryKey: ['analysis-validation', projectId, level],
    queryFn: async () => {
      const response = await fetch(`/analysis?level=${level}`);
      if (!response.ok) throw new Error('Analysis API unavailable');
      return (await response.json()) as Analysis;
    },
  });
  const result = query.data;
  const findings = result?.findings ?? [];
  const blockers = findings.filter((finding) => finding.severity === 'BLOCKER');
  const errors = findings.filter((finding) => finding.severity === 'ERROR');
  const warnings = findings.filter((finding) => finding.severity === 'WARNING');

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
          Week 3–4 Validation
        </h2>
        <button
          onClick={() => void query.refetch()}
          disabled={query.isFetching}
          style={{
            fontSize: 10,
            padding: '3px 10px',
            border: '1px solid #aebac0',
            background: '#ffffff',
            borderRadius: 999,
            cursor: 'pointer',
          }}
        >
          {query.isFetching ? 'running…' : 'Re-run'}
        </button>
      </div>

      <div style={{ marginBottom: 10 }}>
        <span style={pill(!query.isError && blockers.length === 0 && errors.length === 0)}>
          {query.isLoading ? 'LOADING' : blockers.length || errors.length ? `${blockers.length + errors.length} BLOCKING` : 'PASS'}
        </span>
        {warnings.length > 0 && (
          <span style={{ ...pill(false), marginLeft: 6, background: '#faf0de', color: '#7a5a12' }}>
            {warnings.length} W
          </span>
        )}
      </div>

      {query.isError && (
        <div style={{ fontSize: 11, color: '#8b3c32', marginBottom: 8 }}>
          The authoritative analysis API could not be reached.
        </div>
      )}
      {findings.slice(0, 8).map((finding) => (
        <div
          key={finding.id}
          style={{
            fontSize: 11,
            color: finding.severity === 'WARNING' ? '#7a5a12' : '#8b3c32',
            padding: '4px 0',
            lineHeight: 1.35,
          }}
        >
          <strong>{finding.severity}</strong> · {finding.message}
          {finding.suggestedFixes[0] && (
            <div style={{ color: '#65717a', paddingLeft: 10 }}>↳ {finding.suggestedFixes[0]}</div>
          )}
        </div>
      ))}
      {findings.length > 8 && (
        <div style={{ fontSize: 10, color: '#65717a' }}>
          Showing 8 of {findings.length} findings for {level}.
        </div>
      )}
      {!query.isLoading && !query.isError && findings.length === 0 && (
        <div style={{ fontSize: 11, color: '#2d5c36' }}>All Week 3–4 gates cleared.</div>
      )}
    </section>
  );
}