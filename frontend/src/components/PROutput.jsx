import React from 'react';

export default function PROutput({ data }) {
  if (!data) return null;

  return (
    <div className="pr-output" id="pr-output">
      <div className="pr-header">
        <span className="pr-title-text">📦 {data.pr_title}</span>
        {data.branch_name && <span className="pr-branch">🌿 {data.branch_name}</span>}
      </div>

      {data.labels && data.labels.length > 0 && (
        <div className="pr-meta">
          {data.labels.map((label, idx) => (
            <span key={idx} className="pr-label">{label}</span>
          ))}
          {data.reviewers && data.reviewers.map((r, idx) => (
            <span key={`r-${idx}`} className="pr-label" style={{
              background: 'rgba(6, 182, 212, 0.12)',
              color: 'var(--accent-cyan)',
            }}>
              👤 {r}
            </span>
          ))}
          {data.breaking_changes && (
            <span className="pr-label" style={{
              background: 'rgba(239, 68, 68, 0.12)',
              color: 'var(--accent-red)',
            }}>
              ⚠️ Breaking Changes
            </span>
          )}
        </div>
      )}

      <div className="pr-body-content">
        {formatPRBody(data.pr_body)}
      </div>
    </div>
  );
}

function formatPRBody(body) {
  if (!body) return null;

  // Split by lines and render with basic markdown support
  const lines = body.split('\n');
  const elements = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (line.startsWith('## ')) {
      elements.push(<h2 key={i}>{line.replace('## ', '')}</h2>);
    } else if (line.startsWith('### ')) {
      elements.push(
        <h3 key={i} style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginTop: 12, marginBottom: 4 }}>
          {line.replace('### ', '')}
        </h3>
      );
    } else if (line.startsWith('- [ ] ') || line.startsWith('- [x] ')) {
      const checked = line.startsWith('- [x] ');
      const text = line.replace(/^- \[.\] /, '');
      elements.push(
        <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, padding: '2px 0', fontSize: 13 }}>
          <span style={{ opacity: checked ? 1 : 0.5 }}>{checked ? '☑️' : '☐'}</span>
          <span>{text}</span>
        </div>
      );
    } else if (line.startsWith('- ')) {
      elements.push(
        <div key={i} style={{ padding: '2px 0 2px 8px', fontSize: 13, color: 'var(--text-secondary)' }}>
          • {line.replace('- ', '')}
        </div>
      );
    } else if (line.startsWith('| ') && line.includes('|')) {
      // Simple table rendering
      const cells = line.split('|').filter(c => c.trim()).map(c => c.trim());
      if (cells.length > 0 && !cells.every(c => c.match(/^[-:]+$/))) {
        elements.push(
          <div key={i} style={{
            display: 'flex',
            gap: 4,
            padding: '4px 0',
            fontSize: 13,
            borderBottom: '1px solid var(--border-glass)',
          }}>
            {cells.map((cell, ci) => (
              <span key={ci} style={{ flex: 1, fontWeight: cell.startsWith('**') ? 600 : 400 }}>
                {cell.replace(/\*\*/g, '')}
              </span>
            ))}
          </div>
        );
      }
    } else if (line.trim() === '') {
      elements.push(<div key={i} style={{ height: 8 }} />);
    } else if (line.startsWith('*') && line.endsWith('*')) {
      elements.push(
        <div key={i} style={{ fontSize: 12, color: 'var(--text-muted)', fontStyle: 'italic', marginTop: 16 }}>
          {line.replace(/\*/g, '')}
        </div>
      );
    } else if (line.startsWith('---')) {
      elements.push(<hr key={i} style={{ border: 'none', borderTop: '1px solid var(--border-glass)', margin: '12px 0' }} />);
    } else {
      elements.push(
        <div key={i} style={{ fontSize: 13, lineHeight: 1.7 }}>
          {line}
        </div>
      );
    }
    i++;
  }

  return elements;
}
