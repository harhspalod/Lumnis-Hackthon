import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header.jsx';
import PostCard from './components/PostCard.jsx';
import PipelineView from './components/PipelineView.jsx';
import PROutput from './components/PROutput.jsx';

const API_BASE = '/api';

export default function App() {
  const [apiStatus, setApiStatus] = useState(null);
  const [posts, setPosts] = useState([]);
  const [source, setSource] = useState('cache'); // 'live' or 'cache'
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState(null); // post id being processed
  const [pipelineResult, setPipelineResult] = useState(null);
  const [activeStep, setActiveStep] = useState(-1);
  const [error, setError] = useState(null);
  const [warning, setWarning] = useState(null);

  // Check API health on mount
  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then((res) => res.json())
      .then(setApiStatus)
      .catch(() => setApiStatus({ gemini_configured: false, reddit_api_configured: false }));
  }, []);



  // Fetch Reddit posts
  const handleFetchPosts = useCallback(async () => {
    setLoading(true);
    setError(null);
    setPipelineResult(null);
    setActiveStep(-1);
    setProcessing(null);

    try {
      const res = await fetch(`${API_BASE}/posts`);
      if (!res.ok) throw new Error(`Failed to fetch posts (${res.status})`);
      const data = await res.json();
      setPosts(data.posts || []);
      setSource(data.source || 'cache');
      
      if (data.source === 'cache') {
        const msg = data.error === "Reddit credentials not configured" 
          ? "Reddit API credentials not found. Using demo data." 
          : `Reddit fetch failed: ${data.error || 'unknown error'}. Using demo data.`;
        setWarning(msg);
      } else {
        setWarning(null);
      }
    } catch (err) {
      setError(err.message);
      setPosts([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // Process a post through the pipeline
  const handleProcess = useCallback(async (post) => {
    setProcessing(post.id);
    setPipelineResult(null);
    setError(null);

    // Simulate step-by-step progress
    const stepNames = ['classification', 'task', 'code', 'review', 'pr'];
    const stages = {};

    // Show steps progressing
    for (let i = 0; i < stepNames.length; i++) {
      setActiveStep(i);
      // For the first step, also fire the actual API call
      if (i === 0) {
        try {
          const res = await fetch(`${API_BASE}/process`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ post }),
          });
          if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || `Pipeline failed (${res.status})`);
          }
          const result = await res.json();

          if (!result.success) {
            throw new Error(result.error || 'Pipeline failed');
          }

          // Animate steps with data arriving
          const allStages = result.stages || {};

          for (let j = 0; j < stepNames.length; j++) {
            setActiveStep(j);
            // Small delay to visualize each step
            await new Promise((r) => setTimeout(r, 600));
            if (allStages[stepNames[j]]) {
              stages[stepNames[j]] = allStages[stepNames[j]];
              setPipelineResult({ ...result, stages: { ...stages } });
            }
          }

          setActiveStep(-1);
          setPipelineResult(result);
        } catch (err) {
          setError(err.message);
          setActiveStep(-1);
        }
        break;
      }
    }

    setProcessing(null);
  }, []);

  return (
    <div className="app">
      <Header apiStatus={apiStatus} />

      {/* Error Banner */}
      {error && (
        <div className="error-banner" id="error-banner">
          <span>⚠️ {error}</span>
        </div>
      )}

      {/* Warning Banner */}
      {warning && (
        <div className="error-banner warning" style={{ backgroundColor: '#f39c12' }}>
          <span>⚠️ {warning}</span>
        </div>
      )}

      {/* Fetch Section */}
      <div className="fetch-section" id="fetch-section">
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <button
            className="btn-fetch"
            onClick={handleFetchPosts}
            disabled={loading}
            id="fetch-btn"
          >
            {loading ? (
              <>
                <span className="spinner" /> Fetching...
              </>
            ) : (
              `🤖 Fetch Reddit Posts`
            )}
          </button>
        </div>
        <span className="fetch-info">
          {posts.length > 0
            ? `${posts.length} posts loaded (${source === 'live' ? 'LIVE' : 'CACHE'})`
            : 'Fetches real-time posts from selected subreddits'}
        </span>
      </div>

      {/* Posts Grid */}
      {posts.length > 0 && (
        <div className="posts-grid" id="posts-grid">
          {posts.map((post) => (
            <PostCard
              key={post.id}
              post={post}
              isSelected={pipelineResult?.post?.id === post.id}
              isProcessing={processing === post.id}
              onProcess={handleProcess}
            />
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && posts.length === 0 && !pipelineResult && (
        <div className="empty-state" id="empty-state">
          <div className="icon">🤖</div>
          <h3>No Posts Loaded</h3>
          <p>
            Click "Fetch Reddit Posts" to get user complaints and start the AI pipeline.
          </p>
        </div>
      )}

      {/* Pipeline View */}
      {(processing || pipelineResult) && (
        <PipelineView
          stages={pipelineResult?.stages || {}}
          activeStep={activeStep}
        />
      )}

      {/* PR Output */}
      {pipelineResult?.stages?.pr && activeStep === -1 && (
        <div style={{ marginTop: 32 }}>
          <div className="pipeline-title">
            <span>📦 Generated Pull Request</span>
            <div className="line" />
          </div>
          <PROutput data={pipelineResult.stages.pr} />
        </div>
      )}
    </div>
  );
}
