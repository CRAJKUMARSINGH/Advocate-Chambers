import React, { useMemo, useState } from 'react';
import { ProjectLevelSelector } from './components/ProjectLevelSelector';
import { Viewport2D } from './components/Viewport2D';
import { PropertyInspector } from './components/PropertyInspector';
import { ValidationPanel } from './components/ValidationPanel';
import { ArtifactPanel } from './components/ArtifactPanel';
import { ProductModePanel } from './components/ProductModePanel';

type LevelId = 'GF' | 'FF';

export function App(): React.JSX.Element {
  const [projectId] = useState<string>('proj-banswara-bar-association');
  const [level, setLevel] = useState<LevelId>('GF');
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const shellStyle: React.CSSProperties = useMemo(
    () => ({
      display: 'grid',
      gridTemplateRows: '56px 1fr',
      height: '100%',
      width: '100%',
    }),
    [],
  );

  const headerStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    padding: '0 24px',
    background: '#192530',
    color: '#f6f8f8',
    gap: 24,
    borderBottom: '1px solid #0f1820',
  };

  const bodyStyle: React.CSSProperties = {
    display: 'grid',
    gridTemplateColumns: '320px 1fr 360px',
    minHeight: 0,
    gap: 0,
  };

  const sidebarColStyle: React.CSSProperties = {
    background: '#ffffff',
    borderRight: '1px solid #d6dde0',
    overflowY: 'auto',
    padding: 16,
    display: 'flex',
    flexDirection: 'column',
    gap: 16,
  };

  const rightColStyle: React.CSSProperties = {
    ...sidebarColStyle,
    borderRight: 'none',
    borderLeft: '1px solid #d6dde0',
  };

  return (
    <div style={shellStyle}>
      <header style={headerStyle}>
        <div style={{ fontSize: 18, fontWeight: 700, letterSpacing: 0.2 }}>
          ADVOCATE-CHAMBERS
        </div>
        <div style={{ fontSize: 12, opacity: 0.8 }}>
          React 19.3 + TypeScript editor · Python authoritative geometry · Patch 3 shell
        </div>
        <div style={{ marginLeft: 'auto', fontSize: 12, opacity: 0.85 }}>
          project: <code style={{ color: '#9cd3d8' }}>{projectId}</code>
        </div>
      </header>

      <div style={bodyStyle}>
        <aside style={sidebarColStyle}>
          <ProductModePanel />
          <ProjectLevelSelector level={level} onChange={setLevel} />
          <ValidationPanel projectId={projectId} level={level} />
          <ArtifactPanel projectId={projectId} level={level} />
        </aside>

        <main>
          <Viewport2D
            projectId={projectId}
            level={level}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
        </main>

        <aside style={rightColStyle}>
          <PropertyInspector
            projectId={projectId}
            level={level}
            selectedId={selectedId}
          />
        </aside>
      </div>
    </div>
  );
}
