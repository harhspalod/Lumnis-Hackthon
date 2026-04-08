import React from 'react';

export default function PostCard({ post, isSelected, isProcessing, onProcess }) {
  const initial = (post.subreddit || 'R')[0].toUpperCase();
  const date = post.created_at
    ? new Date(post.created_at).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : '';

  return (
    <div
      className={`post-card ${isSelected ? 'selected' : ''} ${isProcessing ? 'processing' : ''}`}
      id={`post-${post.id}`}
    >
      <div className="post-header">
        <div className="post-author">
          <div className="post-avatar" style={{ backgroundColor: '#ff4500' }}>{initial}</div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span className="post-author-name">r/{post.subreddit}</span>
            <span style={{ fontSize: '0.75rem', color: '#888' }}>u/{post.author}</span>
          </div>
        </div>
        <span className="post-date">{date}</span>
      </div>

      <p className="post-text">{post.text}</p>

      {post.metrics && (
        <div className="post-metrics">
          <span className="metric">⬆️ {post.metrics.ups || 0}</span>
          <span className="metric">💬 {post.metrics.comments || 0}</span>
        </div>
      )}

      <div className="post-action">
        <button
          className="btn-process"
          onClick={() => onProcess(post)}
          disabled={isProcessing}
          id={`process-btn-${post.id}`}
        >
          {isProcessing ? (
            <>
              <span className="spinner" /> Processing...
            </>
          ) : (
            '🚀 Process with AI'
          )}
        </button>
      </div>
    </div>
  );
}
