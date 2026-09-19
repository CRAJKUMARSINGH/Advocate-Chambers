import { useState } from 'react';
import type { ReactElement } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';

type Mode = {
  id: string;
  label: string;
  description: string;
};

type Capability = {
  id: string;
  label: string;
  status: 'available' | 'provisional';
  available: boolean;
  modes: string[];
  review: string;
};

type CapabilityResponse = {
  modes: Mode[];
  capabilities: Capability[];
};

type BriefResult = {
  status: string;
  readyForGeneration: boolean;
  facts: {
    units: { detected: string; canonical: string };
    site: { width?: { display: string }; depth?: { display: string } };
    levels: number | null;
    roomSchedule: Array<{ label: string; count: number }>;
    requiredOutputs: string[];
  };
  assumptions: string[];
  ambiguities: string[];
  missingTopologyFacts: string[];
};

const FALLBACK_MODES: Mode[] = [
  { id: 'brief', label: 'Brief', description: 'Compile a brief into typed facts.' },
  { id: 'model', label: 'Model', description: 'Review authoritative geometry.' },
  { id: 'validate', label: 'Validate', description: 'Inspect deterministic findings.' },
  { id: 'furnish', label: 'Furnish', description: 'Place scaled presentation objects.' },
  { id: 'present', label: 'Present', description: 'Compare candidates transparently.' },
  { id: 'export', label: 'Export', description: 'Prepare revision-matched outputs.' },
];

export function ProductModePanel(): ReactElement {
  const [mode, setMode] = useState('brief');
  const [brief, setBrief] = useState(
    'site 60m x 30m, north is north, road frontage east, 2 levels, public access, outputs PDF DXF',
  );
  const capabilities = useQuery<CapabilityResponse>({
    queryKey: ['product-capabilities'],
    queryFn: async () => {
      const response = await fetch('/capabilities');
      if (!response.ok) throw new Error('capabilities unavailable');
      return (await response.json()) as CapabilityResponse;
    },
    staleTime: 60_000,
  });
  const compile = useMutation<BriefResult, Error, string>({
    mutationFn: async (text) => {
      const response = await fetch('/brief/compile', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ text, defaultUnits: 'metric' }),
      });
      if (!response.ok) throw new Error('brief compiler unavailable');
      return (await response.json()) as BriefResult;
    },
  });
  const modes = capabilities.data?.modes ?? FALLBACK_MODES;
  const active = modes.find((item) => item.id === mode) ?? modes[0];
  const statusColor = (status: string): string =>
    status === 'available' ? '#236b52' : status === 'provisional' ? '#9b6a18' : '#65717a';

  return (
    <section style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div>
        <h2 style={{ margin: 0, fontSize: 12, textTransform: 'uppercase', letterSpacing: 1.2, color: '#65717a' }}>
          Product modes
        </h2>
        <p style={{ margin: '4px 0 0', fontSize: 11, color: '#65717a' }}>
          Every mode reads the same canonical model. Presentation objects never become building geometry.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 4 }}>
        {modes.map((item) => (
          <button
            key={item.id}
            onClick={() => setMode(item.id)}
            title={item.description}
            style={{
              border: mode === item.id ? '1px solid #2e5c62' : '1px solid #d6dde0',
              background: mode === item.id ? '#eaf4f3' : '#ffffff',
              color: '#192530',
              borderRadius: 4,
              padding: '6px 3px',
              fontSize: 10,
              fontWeight: mode === item.id ? 700 : 500,
              cursor: 'pointer',
            }}
          >
            {item.label}
          </button>
        ))}
      </div>

      <div style={{ border: '1px solid #d6dde0', borderRadius: 5, padding: 9, background: '#fbfcfc' }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: '#192530' }}>{active?.label} mode</div>
        <div style={{ marginTop: 3, fontSize: 11, color: '#65717a' }}>{active?.description}</div>
      </div>

      {mode === 'brief' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <textarea
            value={brief}
            onChange={(event) => setBrief(event.target.value)}
            rows={4}
            aria-label="Natural-language architectural brief"
            style={{ resize: 'vertical', border: '1px solid #c7d0d4', borderRadius: 5, padding: 8, fontSize: 11, fontFamily: 'inherit' }}
          />
          <button
            onClick={() => compile.mutate(brief)}
            disabled={compile.isPending || !brief.trim()}
            style={{ border: '1px solid #2e5c62', background: '#2e5c62', color: '#ffffff', borderRadius: 5, padding: '8px 10px', fontSize: 11, fontWeight: 700, cursor: 'pointer' }}
          >
            {compile.isPending ? 'Compiling brief…' : 'Compile brief'}
          </button>
          {compile.isError && <div style={{ fontSize: 11, color: '#8b3c32' }}>{compile.error.message}</div>}
          {compile.data && (
            <div style={{ borderLeft: `3px solid ${compile.data.readyForGeneration ? '#236b52' : '#9b6a18'}`, paddingLeft: 8, fontSize: 11 }}>
              <strong>{compile.data.readyForGeneration ? 'Ready for review' : 'Topology facts needed'}</strong>
              <div style={{ marginTop: 4, color: '#65717a' }}>
                {compile.data.facts.site.width?.display ?? 'site width missing'} · {compile.data.facts.levels ?? 'levels missing'} levels · {compile.data.facts.roomSchedule.length} room types
              </div>
              {compile.data.missingTopologyFacts.slice(0, 3).map((item) => (
                <div key={item} style={{ marginTop: 3, color: '#8b3c32' }}>• {item}</div>
              ))}
            </div>
          )}
        </div>
      )}

      <div>
        <div style={{ fontSize: 11, fontWeight: 700, marginBottom: 5 }}>Capability matrix</div>
        {(capabilities.data?.capabilities ?? []).map((item) => (
          <div key={item.id} style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 6, padding: '4px 0', borderTop: '1px solid #edf0f1', fontSize: 10 }}>
            <span title={item.review}>{item.label}</span>
            <span style={{ color: statusColor(item.status), fontWeight: 700 }}>{item.status}</span>
          </div>
        ))}
        {!capabilities.data && <div style={{ fontSize: 10, color: '#65717a' }}>Capability matrix is available when the API is online.</div>}
      </div>
    </section>
  );
}