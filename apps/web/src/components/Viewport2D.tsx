import React, { useMemo } from 'react';

interface Props {
  projectId: string;
  level: 'GF' | 'FF';
  selectedId: string | null;
  onSelect: (id: string | null) => void;
}

export function Viewport2D({ projectId, level, selectedId, onSelect }: Props): JSX.Element {
  const vpStyle: React.CSSProperties = useMemo(
    () => ({
      width: '100%',
      height: '100%',
      background:
        'radial-gradient(circle at 20% 20%, #ffffff 0%, #eef4f4 100%)',
      position: 'relative' as const,
      overflow: 'hidden',
    }),
    [],
  );

  const plan: { spaces: { id: string; name: string; x: number; y: number; w: number; h: number }[] } = useMemo(() => {
    if (level === 'GF') {
      return {
        spaces: [
          { id: 'GF-01', name: 'Entry Lobby', x: 40, y: 40, w: 420, h: 110 },
          { id: 'GF-02', name: 'Bar Office', x: 40, y: 160, w: 210, h: 120 },
          { id: 'GF-03', name: 'Common Toilet', x: 260, y: 160, w: 210, h: 120 },
          { id: 'GF-04', name: 'Main Hall', x: 40, y: 300, w: 640, h: 620 },
          { id: 'GF-05', name: 'President', x: 40, y: 930, w: 224, h: 168 },
          { id: 'GF-06', name: 'Secretary', x: 272, y: 930, w: 210, h: 168 },
          { id: 'GF-STAIR', name: 'ST-01 Dog-Leg', x: 690, y: 300, w: 126, h: 462 },
        ],
      };
    }
    return {
      spaces: [
        { id: 'FF-01', name: 'FF Lobby', x: 40, y: 40, w: 420, h: 110 },
        { id: 'FF-02', name: 'Pantry', x: 40, y: 160, w: 210, h: 120 },
        { id: 'FF-03', name: 'Store', x: 260, y: 160, w: 210, h: 120 },
        { id: 'FF-EDP', name: 'EDP Centre', x: 40, y: 330, w: 210, h: 200 },
        { id: 'FF-04', name: 'Library Reading', x: 260, y: 330, w: 434, h: 690 },
        { id: 'FF-05', name: 'Librarian Cabin', x: 40, y: 550, w: 210, h: 210 },
        { id: 'FF-06', name: 'Admin Office', x: 40, y: 780, w: 210, h: 280 },
        { id: 'FF-STAIR', name: 'ST-01 Stacked', x: 690, y: 300, w: 126, h: 462 },
      ],
    };
  }, [level]);

  const titleBarStyle: React.CSSProperties = {
    position: 'absolute',
    top: 12,
    left: 16,
    right: 16,
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: 11,
    color: '#65717a',
    pointerEvents: 'none' as const,
  };

  return (
    <div style={vpStyle} onClick={() => onSelect(null)}>
      <div style={titleBarStyle}>
        <div>
          <strong style={{ color: '#192530' }}>2D VIEWPORT</strong> ·{' '}
          <span>patch 3 shell · SVG placeholder · geometry authoritative on Python</span>
        </div>
        <div>
          {level} · <code>{projectId}</code>
        </div>
      </div>

      <svg
        viewBox="0 0 880 1140"
        preserveAspectRatio="xMidYMid meet"
        style={{
          position: 'absolute',
          inset: 48,
          width: 'calc(100% - 96px)',
          height: 'calc(100% - 96px)',
          border: '1px solid #aebac0',
          boxShadow: '0 1px 0 rgba(25,37,48,0.04) inset',
          background: '#ffffff',
        }}
      >
        <defs>
          <pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse">
            <path d="M 30 0 L 0 0 0 30" fill="none" stroke="#eef4f4" strokeWidth="0.8" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />

        {plan.spaces.map((s) => {
          const isSel = selectedId === s.id;
          return (
            <g
              key={s.id}
              onClick={(e) => {
                e.stopPropagation();
                onSelect(s.id);
              }}
              style={{ cursor: 'pointer' }}
            >
              <rect
                x={s.x}
                y={s.y}
                width={s.w}
                height={s.h}
                fill={isSel ? '#f4e9d9' : s.id.includes('STAIR') ? '#f5eee5' : '#f6f8f8'}
                stroke={isSel ? '#8b3c32' : '#718087'}
                strokeWidth={isSel ? 2.4 : 1.1}
                rx={2}
              />
              <text
                x={s.x + s.w / 2}
                y={s.y + s.h / 2}
                textAnchor="middle"
                fontSize={11}
                fontWeight={600}
                fill="#192530"
              >
                {s.name}
              </text>
              <text
                x={s.x + s.w / 2}
                y={s.y + s.h / 2 + 14}
                textAnchor="middle"
                fontSize={9}
                fill="#65717a"
              >
                {s.id}
              </text>
            </g>
          );
        })}

        <text x="16" y="1120" fontSize="9" fill="#65717a">
          1" = 1'-0" approx · review on Python-generated PDF/DXF for signed dimensions
        </text>
      </svg>
    </div>
  );
}
