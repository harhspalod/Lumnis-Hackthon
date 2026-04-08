import React from 'react';

const STEPS = [
  { key: 'classification', name: 'Classify Feedback', icon: '🏷️' },
  { key: 'task', name: 'Generate Task', icon: '📋' },
  { key: 'code', name: 'Generate Code', icon: '💻' },
  { key: 'review', name: 'Code Review', icon: '🔍' },
  { key: 'pr', name: 'Pull Request', icon: '📦' },
];

function ClassificationView({ data }) {
  const typeClass = data.issue_type === 'Bug' ? 'bug' : data.issue_type === 'Performance' ? 'performance' : 'feature';
  const prioClass = data.priority?.toLowerCase() || 'medium';

  return (
    <div className="classification-result">
      <span className={`class-tag ${typeClass}`}>
        {data.issue_type === 'Bug' ? '🐛' : data.issue_type === 'Performance' ? '⚡' : '✨'}
        {data.issue_type}
      </span>
      <span className={`class-tag ${prioClass}`}>
        {data.priority === 'High' ? '🔴' : data.priority === 'Medium' ? '🟡' : '🟢'}
        {data.priority} Priority
      </span>
      {data.affected_component && (
        <span className="class-tag feature">📂 {data.affected_component}</span>
      )}
      {data.summary && <p className="class-summary">{data.summary}</p>}
      {data.user_impact && (
        <p className="class-summary" style={{ opacity: 0.8, marginTop: 4 }}>
          <strong>Impact:</strong> {data.user_impact}
        </p>
      )}
    </div>
  );
}

function TaskView({ data }) {
  return (
    <div className="task-display">
      <h4>{data.task_title}</h4>
      <p>{data.description}</p>
      {data.acceptance_criteria && (
        <>
          <h5 style={{ fontSize: 13, fontWeight: 600, marginBottom: 6, color: 'var(--text-primary)' }}>
            Acceptance Criteria
          </h5>
          <ul className="task-criteria">
            {data.acceptance_criteria.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </>
      )}
      {data.technical_notes && (
        <p style={{ fontSize: 12, color: 'var(--accent-cyan)', marginTop: 10, fontStyle: 'italic' }}>
          💡 {data.technical_notes}
        </p>
      )}
      {data.labels && (
        <div className="task-labels">
          {data.labels.map((l, i) => (
            <span key={i} className="task-label">{l}</span>
          ))}
        </div>
      )}
    </div>
  );
}

function CodeView({ data }) {
  return (
    <div className="code-block">
      <div className="code-header">
        <span className="code-filename">{data.filename}</span>
        <span className="code-language">{data.language}</span>
      </div>
      <div className="code-content">
        <pre>{data.code}</pre>
      </div>
      {data.explanation && <p className="code-explanation">💡 {data.explanation}</p>}
    </div>
  );
}

function ReviewView({ data }) {
  const score = data.overall_score || 0;
  const scoreClass = score >= 7 ? 'good' : score >= 5 ? 'ok' : 'bad';
  const verdictClass = data.verdict?.includes('Approved') ? 'approved' : 'changes';

  return (
    <div className="review-display">
      <div className="review-header">
        <div className="review-score">
          <div className={`score-circle ${scoreClass}`}>{score}</div>
          <div>
            <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>Quality Score</div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>out of 10</div>
          </div>
        </div>
        <span className={`review-verdict ${verdictClass}`}>{data.verdict}</span>
      </div>

      {data.strengths && data.strengths.length > 0 && (
        <div className="review-strengths">
          <h5>✅ Strengths</h5>
          <ul>
            {data.strengths.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      )}

      {data.issues && data.issues.length > 0 && (
        <div className="review-issues">
          <h5>📝 Review Comments</h5>
          {data.issues.map((issue, i) => (
            <div key={i} className={`review-issue-item ${issue.severity}`}>
              <div className={`issue-severity ${issue.severity}`}>{issue.severity}</div>
              <div className="issue-desc">{issue.description}</div>
              {issue.suggestion && <div className="issue-suggestion">💡 {issue.suggestion}</div>}
            </div>
          ))}
        </div>
      )}

      {data.summary && <div className="review-summary-text">{data.summary}</div>}
    </div>
  );
}

function LoadingContent() {
  return (
    <div>
      <div className="loading-skeleton wide" />
      <div className="loading-skeleton medium" />
      <div className="loading-skeleton narrow" />
    </div>
  );
}

export default function PipelineView({ stages, activeStep }) {
  const renderStepContent = (step) => {
    const data = stages[step.key];
    if (!data) return null;

    switch (step.key) {
      case 'classification': return <ClassificationView data={data} />;
      case 'task': return <TaskView data={data} />;
      case 'code': return <CodeView data={data} />;
      case 'review': return <ReviewView data={data} />;
      case 'pr': return null; // PR is rendered separately
      default: return <pre>{JSON.stringify(data, null, 2)}</pre>;
    }
  };

  return (
    <div className="pipeline-section" id="pipeline-view">
      <div className="pipeline-title">
        <span>⚙️ AI Pipeline</span>
        <div className="line" />
      </div>

      <div className="pipeline-steps">
        {STEPS.map((step, idx) => {
          const hasData = !!stages[step.key];
          const isActive = activeStep === idx;
          const isCompleted = hasData && !isActive;
          const status = isActive ? 'active' : isCompleted ? 'completed' : '';

          return (
            <div key={step.key} className={`pipeline-step ${status}`} id={`step-${step.key}`}>
              <div className="step-indicator">
                {isCompleted ? '✓' : isActive ? '⟳' : idx + 1}
              </div>

              <div className="step-header">
                <span className="step-name">{step.icon} {step.name}</span>
                <span className={`step-badge ${isActive ? 'active' : isCompleted ? 'done' : 'pending'}`}>
                  {isActive ? 'Running...' : isCompleted ? 'Done' : 'Pending'}
                </span>
              </div>

              {isActive && (
                <div className="step-content">
                  <LoadingContent />
                </div>
              )}

              {isCompleted && step.key !== 'pr' && (
                <div className="step-content">
                  {renderStepContent(step)}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
