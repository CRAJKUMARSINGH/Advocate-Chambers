import React, { useEffect, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';

interface Props {
  projectId: string;
  level: 'GF' | 'FF';
}

type JobStatus = {
  jobId: string;
  status: string;
  progress: number;
  startedAt: string | null;
  finishedAt: string | null;
  artifactIds: string[];
  error: string | null;
};

export function ArtifactPanel({ projectId, level }: Props): JSX.Element {
  const [jobId, setJobId] = useState<string | null>(null);

  const start = useMutation({
    mutationFn: async () => {
      const res = await fetch('/generate', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          projectId,
          pipeline: 'refined',
          level,
          sheetSize: 'A4',
        }),
      });
      const data = (await res.json()) as { jobId: string; status: string };
      return data;
    },
    onSuccess: (data) => setJobId(data.jobId),
  });

  const jobQuery = useQuery<JobStatus>({
    queryKey: ['job', jobId],
    enabled: !!jobId,
    queryFn: async () => {
      const res = await fetch(`/jobs/${jobId}`);
      return (await res.json()) as JobStatus;
    },
    refetchInterval: (q) => (q.state.data?.status === 'done' ? false : 1200),
  });

  useEffect(() => {
    void jobQuery.refetch();
  }, [jobId]);  // eslint-disable-line react-hooks/exhaustive-deps

  const progress = jobQuery.data?.progress ?? 0;

  return (
    <section>
      <h2 style={{ margin: '0 0 8px 0', fontSize: 12, textTransform: 'uppercase', letterSpacing: 1.2, color: '#65717a' }}>
        Artifacts / Jobs
      </h2>

      <button
        onClick={() => start.mutate()}
        disabled={start.isPending || jobQuery.isFetching}
        style={{
          width: '100%',
          padding: '10px 12px',
          borderRadius: 6,
          border: 'none',
          background: '#2e5c62',
          color: '#ffffff',
          fontWeight: 700,
          fontSize: 12,
          cursor: start.isPending ? 'wait' : 'pointer',
          marginBottom: 10,
        }}
      >
        {start.isPending
          ? 'Queueing generation…'
          : `Generate DXF+PDF (${level})`}
      </button>

      {jobId && (
        <div style={{ fontSize: 11, color: '#65717a', marginBottom: 8 }}>
          job: <code>{jobId}</code>
        </div>
      )}
      {jobId && (
        <div
          style={{
            height: 6,
            borderRadius: 999,
            background: '#eef4f4',
            overflow: 'hidden',
            marginBottom: 10,
          }}
        >
          <div
            style={{
              width: `${progress}%`,
              height: '100%',
              background: '#2e5c62',
              transition: 'width 220ms ease',
            }}
          />
        </div>
      )}

      {jobQuery.data?.status === 'done' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {jobQuery.data.artifactIds.map((aid) => (
            <a
              key={aid}
              href={`/artifacts/${aid}`}
              target="_blank"
              rel="noreferrer"
              style={{
                padding: '8px 10px',
                borderRadius: 6,
                border: '1px solid #c7d0d4',
                background: '#f6f8f8',
                textDecoration: 'none',
                color: '#192530',
                fontSize: 11,
                fontWeight: 600,
              }}
            >
              ⬇ {aid}
            </a>
          ))}
        </div>
      )}

      {!jobId && (
        <div style={{ fontSize: 11, color: '#65717a', lineHeight: 1.5 }}>
          The Python CAD engine produces:
          <ul style={{ margin: '6px 0 0 16px', padding: 0 }}>
            <li>R2018 DXF (ezdxf) · A4 Portrait 90°</li>
            <li>Archival PDF (PyMuPDF fitted · 10mm margin)</li>
            <li>A2 Landscape review set (reportlab)</li>
          </ul>
        </div>
      )}
    </section>
  );
}
