import { useState } from 'react';
import {
  Sparkles,
  Plus,
  ClipboardList,
  Diamond,
  Settings,
  CircleHelp,
  ChevronDown,
  ChevronUp,
  FileText,
  Search,
  Layers,
  ChartNoAxesColumn,
  UserRound,
  Check,
  X,
  Info,
  PanelLeftClose,
  PanelLeftOpen,
  CircleDot,
  List,
  Database,
  CheckCircle2,
} from 'lucide-react';
import './App.css';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

function App() {
  const [requirement, setRequirement] = useState('');
  const [analysisOpen, setAnalysisOpen] = useState(false);
  const [reviewOpen, setReviewOpen] = useState(false);
  const [expandedCases, setExpandedCases] = useState<Record<string, boolean>>(
    {},
  );
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [workflowResult, setWorkflowResult] = useState<any>(null);
  const [decisionLoading, setDecisionLoading] = useState(false);
  const [decisionError, setDecisionError] = useState('');

  const [jiraLoading, setJiraLoading] = useState(false);
  const [jiraError, setJiraError] = useState('');
  const [jiraResult, setJiraResult] = useState<any>(null);

  function toggleCase(id: string) {
    setExpandedCases((current) => ({
      ...current,
      [id]: !current[id],
    }));
  }

  async function handleGenerate() {
    if (!requirement.trim()) {
      setError('Please enter a software requirement.');
      return;
    }

    setLoading(true);
    setError('');
    setWorkflowResult(null);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/agent/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          requirement: requirement,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate test cases.');
      }

      const data = await response.json();

      setWorkflowResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  }

  async function handleHumanDecision(decision: 'approve' | 'reject') {
    if (!workflowResult?.test_run_id) {
      setDecisionError('No test run is available for review.');
      return;
    }

    setDecisionLoading(true);
    setDecisionError('');

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/agent/runs/${workflowResult.test_run_id}/${decision}`,
        {
          method: 'POST',
        },
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || `Failed to ${decision} test run.`);
      }

      setWorkflowResult((current: any) => ({
        ...current,
        human_approved: data.human_approved,
        human_decision: data.human_decision,
      }));
    } catch (err) {
      setDecisionError(
        err instanceof Error ? err.message : 'Something went wrong.',
      );
    } finally {
      setDecisionLoading(false);
    }
  }

  async function handleCreateJiraIssues() {
    if (!workflowResult?.test_run_id) {
      setJiraError('No test run is available.');
      return;
    }

    setJiraLoading(true);
    setJiraError('');
    setJiraResult(null);

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/agent/runs/${workflowResult.test_run_id}/create-jira-issues`,
        {
          method: 'POST',
        },
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to create Jira issues.');
      }

      setJiraResult(data);
    } catch (err) {
      setJiraError(
        err instanceof Error ? err.message : 'Something went wrong.',
      );
    } finally {
      setJiraLoading(false);
    }
  }

  return (
    <div className="dashboard">
      {/* TOP NAVIGATION */}
      <header className="topbar">
        <div className="topbar-brand">
          <Sparkles size={27} />
          <span>QAgenius</span>
          <div className="brand-divider" />
          <span className="product-description">
            AI-Powered Test Case Generation
          </span>
        </div>

        <div className="topbar-actions">
          <button className="icon-button" disabled title="Coming soon">
            <CircleHelp size={21} />
          </button>
          <div className="profile">
            <div className="avatar">J</div>
            <span>Profile</span>
            <ChevronDown size={15} />
          </div>
        </div>
      </header>

      <div className="dashboard-body">
        {/* SIDEBAR */}
        {sidebarOpen && (
          <aside className="sidebar">
            <button className="new-run-button">
              <Plus size={21} />
              New Test Run
            </button>

            <nav className="sidebar-nav">
              <button disabled>
                <ClipboardList size={20} />
                Test Run History
                <span className="coming-soon">Soon</span>
              </button>

              <button disabled>
                <Diamond size={20} />
                Jira Issues
                <span className="coming-soon">Soon</span>
              </button>

              <button disabled>
                <Settings size={20} />
                Settings
              </button>
            </nav>

            <div className="sidebar-footer">
              <div className="footer-decoration">
                <svg viewBox="0 0 260 100" preserveAspectRatio="none">
                  <path d="M0 55 C70 0 100 110 160 45 S220 20 260 50" />
                  <path d="M0 68 C70 13 100 123 160 58 S220 33 260 63" />
                  <path d="M0 81 C70 26 100 136 160 71 S220 46 260 76" />
                </svg>
              </div>
              <h3>QAgenius</h3>
              <p>
                From Requirements
                <br />
                to Test Cases to Jira
                <br />— with AI
              </p>
            </div>
          </aside>
        )}

        {/* MAIN WORKSPACE */}
        <main className="main-workspace">
          <div className="workspace-heading">
            <button
              className="icon-button sidebar-toggle"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              title="Toggle sidebar"
            >
              {sidebarOpen ? (
                <PanelLeftClose size={19} />
              ) : (
                <PanelLeftOpen size={19} />
              )}
            </button>
            <div>
              <h1>Generate Test Cases</h1>
              <p>
                Enter a requirement and let Claude analyze, generate, review,
                and refine test cases for you.
              </p>
            </div>
          </div>

          {/* REQUIREMENT INPUT */}
          <section className="requirement-box">
            <textarea
              value={requirement}
              onChange={(e) => setRequirement(e.target.value)}
              placeholder="e.g. As a user, I want to reset my password so that I can regain access to my account."
            />
            <div className="requirement-actions">
              <span className="input-hint">
                Describe your software requirement
              </span>
              <button
                className="primary-button"
                onClick={handleGenerate}
                disabled={loading || !requirement.trim()}
              >
                <Sparkles size={17} />
                {loading ? 'Generating...' : 'Generate Test Cases'}
              </button>
            </div>
          </section>

          {/* ANALYSIS AND REVIEW */}
          <section className="collapsible-row">
            {/* REQUIREMENT ANALYSIS */}
            <div
              className={`collapsible-wrapper ${analysisOpen ? 'expanded' : 'collapsed'}`}
            >
              <button
                type="button"
                className="collapsible-header"
                onClick={() => setAnalysisOpen((prev) => !prev)}
              >
                <FileText size={21} />
                <span>Requirement Analysis</span>

                {analysisOpen ? (
                  <ChevronUp size={19} />
                ) : (
                  <ChevronDown size={19} />
                )}
              </button>

              {analysisOpen && (
                <div className="collapsible-content">
                  {workflowResult?.analysis ? (
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {workflowResult.analysis}
                    </ReactMarkdown>
                  ) : (
                    <p>
                      Requirement analysis will appear here after generation.
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* AI REVIEW */}
            <div
              className={`collapsible-wrapper ${reviewOpen ? 'expanded' : 'collapsed'}`}
            >
              <button
                type="button"
                className="collapsible-header"
                onClick={() => setReviewOpen((prev) => !prev)}
              >
                <Search size={21} />
                <span>AI Review</span>

                <span
                  className={`status-badge ${
                    workflowResult?.status === 'approved'
                      ? 'success'
                      : workflowResult?.status === 'needs_improvement'
                        ? 'warning'
                        : 'neutral'
                  }`}
                >
                  {workflowResult?.status
                    ? workflowResult.status.replace('_', ' ')
                    : 'Awaiting'}
                </span>

                {reviewOpen ? (
                  <ChevronUp size={19} />
                ) : (
                  <ChevronDown size={19} />
                )}
              </button>

              {reviewOpen && (
                <div className="collapsible-content">
                  {workflowResult?.review ? (
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {workflowResult.review}
                    </ReactMarkdown>
                  ) : (
                    <p>AI review feedback will appear here after generation.</p>
                  )}
                </div>
              )}
            </div>
          </section>

          {/* TEST CASES */}
          <section className="test-cases-section">
            <div className="section-heading">
              <div className="section-title">
                <Layers size={22} />
                <h2>Generated Test Cases</h2>
                <span className="count-badge">
                  {workflowResult?.test_cases?.length ?? 0}
                </span>
                <span className="preview-label">Design preview</span>
              </div>

              <div className="expand-actions">
                <button onClick={() => setExpandedCases({})}>
                  <ChevronUp size={15} /> Collapse All
                </button>

                <button
                  onClick={() => {
                    const testCases = workflowResult?.test_cases ?? [];

                    setExpandedCases(
                      Object.fromEntries(
                        testCases.map((testCase: any) => [testCase.id, true]),
                      ),
                    );
                  }}
                >
                  <ChevronDown size={15} /> Expand All
                </button>
              </div>
            </div>

            {workflowResult ? (
              workflowResult.test_cases?.length > 0 ? (
                workflowResult.test_cases.map((testCase: any) => (
                  <article className="test-case-card" key={testCase.id}>
                    <button
                      className="test-case-header"
                      onClick={() => toggleCase(testCase.id)}
                    >
                      <span className="test-case-title">
                        {testCase.id} · {testCase.scenario}
                      </span>

                      <div className="test-case-tags">
                        <span className="type-badge">{testCase.test_type}</span>

                        <span className="priority-badge">
                          {testCase.priority}
                        </span>

                        {expandedCases[testCase.id] ? (
                          <ChevronUp size={19} />
                        ) : (
                          <ChevronDown size={19} />
                        )}
                      </div>
                    </button>

                    {expandedCases[testCase.id] && (
                      <div className="test-case-content">
                        <div className="detail-row">
                          <div className="detail-label">
                            <CircleDot size={19} />
                            <span>Preconditions</span>
                          </div>
                          <div>{testCase.preconditions}</div>
                        </div>

                        <div className="detail-row">
                          <div className="detail-label">
                            <List size={19} />
                            <span>Test Steps</span>
                          </div>
                          <div>
                            <ol>
                              {testCase.steps.map(
                                (step: string, index: number) => (
                                  <li key={index}>{step}</li>
                                ),
                              )}
                            </ol>
                          </div>
                        </div>

                        <div className="detail-row">
                          <div className="detail-label">
                            <Database size={19} />
                            <span>Test Data</span>
                          </div>
                          <div>{testCase.test_data}</div>
                        </div>

                        <div className="detail-row">
                          <div className="detail-label">
                            <CheckCircle2 size={19} />
                            <span>Expected Result</span>
                          </div>
                          <div>{testCase.expected_result}</div>
                        </div>
                      </div>
                    )}
                  </article>
                ))
              ) : (
                <div className="empty-state">No test cases were generated.</div>
              )
            ) : (
              <div className="empty-state">
                Your generated test cases will appear here.
              </div>
            )}
          </section>
        </main>

        {/* RIGHT SUMMARY PANEL */}
        <aside className="right-panel">
          <section className="panel-card summary-card">
            <div className="panel-heading">
              <ChartNoAxesColumn size={21} />
              <h3>Test Run Summary</h3>
            </div>

            <div className="summary-row">
              <span>Test Run ID</span>
              <strong>{workflowResult?.test_run_id ?? '—'}</strong>
            </div>

            <div className="summary-row">
              <span>Total Test Cases</span>
              <strong>{workflowResult?.test_cases?.length ?? '—'}</strong>
            </div>

            <div className="summary-row">
              <span>High Priority</span>
              <strong>
                {workflowResult?.test_cases
                  ? workflowResult.test_cases.filter(
                      (tc: any) => tc.priority === 'High',
                    ).length
                  : '—'}
              </strong>
            </div>

            <div className="summary-row">
              <span>Medium Priority</span>
              <strong>
                {workflowResult?.test_cases
                  ? workflowResult.test_cases.filter(
                      (tc: any) => tc.priority === 'Medium',
                    ).length
                  : '—'}
              </strong>
            </div>

            <div className="summary-row">
              <span>Low Priority</span>
              <strong>
                {workflowResult?.test_cases
                  ? workflowResult.test_cases.filter(
                      (tc: any) => tc.priority === 'Low',
                    ).length
                  : '—'}
              </strong>
            </div>

            <div className="summary-row">
              <span>AI Decision</span>
              <span
                className={`status-badge ${
                  workflowResult?.status === 'approved'
                    ? 'success'
                    : workflowResult?.status === 'needs_improvement'
                      ? 'warning'
                      : 'neutral'
                }`}
              >
                {workflowResult?.status
                  ? workflowResult.status.replace('_', ' ')
                  : 'Pending'}
              </span>
            </div>

            <div className="summary-row">
              <span>Human Decision</span>
              <span
                className={`status-badge ${
                  workflowResult?.human_decision === 'approved'
                    ? 'success'
                    : workflowResult?.human_decision === 'rejected'
                      ? 'warning'
                      : 'pending'
                }`}
              >
                {workflowResult?.human_decision ?? 'Pending'}
              </span>
            </div>

            <div className="summary-row">
              <span>Improvement Iterations</span>
              <strong>{workflowResult?.iteration ?? '—'}</strong>
            </div>
          </section>

          <section className="panel-card human-review-card">
            <div className="panel-heading">
              <UserRound size={22} />
              <h3>Human Review</h3>
            </div>

            <div className="review-notice">
              <Info size={20} />
              <p>
                Review the generated test cases before deciding whether to
                proceed with Jira creation.
              </p>
            </div>

            {decisionError && <p className="error-message">{decisionError}</p>}

            <div className="review-actions">
              <button
                className="approve-button"
                disabled={
                  !workflowResult?.test_run_id ||
                  decisionLoading ||
                  workflowResult?.human_decision !== undefined
                }
                onClick={() => handleHumanDecision('approve')}
              >
                <Check size={19} />
                {decisionLoading ? 'Processing...' : 'Approve'}
              </button>

              <button
                className="reject-button"
                disabled={
                  !workflowResult?.test_run_id ||
                  decisionLoading ||
                  workflowResult?.human_decision !== undefined
                }
                onClick={() => handleHumanDecision('reject')}
              >
                <X size={19} />
                Reject
              </button>
            </div>

            {workflowResult?.human_decision && (
              <div className="review-notice">
                <CheckCircle2 size={20} />
                <p>
                  Human decision:{' '}
                  <strong>{workflowResult.human_decision}</strong>
                </p>
              </div>
            )}
          </section>

          <section className="panel-card jira-card">
            <div className="panel-heading">
              <Diamond size={21} />
              <h3>Create Jira Issues</h3>
            </div>

            <p>
              Create Jira tasks for the generated test cases after human
              approval.
            </p>

            <button
              className="approve-button"
              disabled={
                workflowResult?.human_decision !== 'approved' || jiraLoading
              }
              onClick={handleCreateJiraIssues}
            >
              <Diamond size={19} />
              {jiraLoading ? 'Creating Jira Issues...' : 'Create Jira Issues'}
            </button>

            {workflowResult?.human_decision !== 'approved' && (
              <span className="future-label">
                Approve the test cases first to enable Jira creation.
              </span>
            )}

            {jiraError && <p className="error-message">{jiraError}</p>}

            {jiraResult && (
              <div className="jira-results">
                <h4>Jira Creation Summary</h4>

                <p>Created: {jiraResult.created_count}</p>
                <p>Skipped: {jiraResult.skipped_count}</p>
                <p>Failed: {jiraResult.failed_count}</p>

                {jiraResult.created_issues?.map((issue: any) => (
                  <p key={issue.test_case_id}>
                    {issue.test_case_id}:{' '}
                    <strong>{issue.jira_issue_key}</strong>
                  </p>
                ))}

                {jiraResult.existing_issues?.map((issue: any) => (
                  <p key={issue.test_case_id}>
                    {issue.test_case_id}:{' '}
                    <strong>{issue.jira_issue_key}</strong> (Already exists)
                  </p>
                ))}

                {jiraResult.failed_issues?.map((issue: any) => (
                  <p key={issue.test_case_id} className="error-message">
                    {issue.test_case_id}: {issue.error}
                  </p>
                ))}
              </div>
            )}
          </section>
        </aside>
      </div>
    </div>
  );
}

export default App;
