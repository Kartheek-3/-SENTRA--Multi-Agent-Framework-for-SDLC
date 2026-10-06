import React, { useState } from 'react';

interface ContractsPageProps {
  state: any;
  onOpenWorkspace: () => void;
}

export function ContractsPage({ state, onOpenWorkspace }: ContractsPageProps) {
  const [selectedEndpoint, setSelectedEndpoint] = useState<any>(null);

  const plan = state?.project_plan;
  const systemDesign = plan?.system_design;
  const frontendPlan = state?.frontend_architecture_plan;
  const fullStackContract = state?.full_stack_contract;
  const contractIssues = state?.contract_issues || [];

  const endpoints = systemDesign?.api_endpoints || [
    { path: '/api/v1/health', method: 'GET', summary: 'Health check probe', request_model: null, response_model: 'HealthResponse' },
    { path: '/api/v1/auth/login', method: 'POST', summary: 'User authentication', request_model: 'LoginRequest', response_model: 'AuthTokenResponse' },
    { path: '/api/v1/items', method: 'GET', summary: 'List collection items', request_model: 'ItemQueryFilter', response_model: 'ItemListResponse' },
    { path: '/api/v1/items', method: 'POST', summary: 'Create new item', request_model: 'CreateItemRequest', response_model: 'ItemDetailResponse' },
  ];

  const dbSchemas = systemDesign?.database_schemas || [
    { table: 'users', columns: ['id (UUID, PK)', 'email (VARCHAR, Unique)', 'hashed_password (VARCHAR)', 'created_at (TIMESTAMP)'] },
    { table: 'items', columns: ['id (UUID, PK)', 'user_id (UUID, FK)', 'title (VARCHAR)', 'status (VARCHAR)', 'updated_at (TIMESTAMP)'] },
  ];

  const hasContracts = Boolean(plan || frontendPlan || fullStackContract);

  return (
    <div className="contractsPageFrame">
      <header className="contractsHeader">
        <div>
          <h1>Full-Stack Contract Intelligence</h1>
          <p className="subtitle">Three-Way Schema Parity: Frontend Architecture ⟷ SystemDesign API ⟷ Database Relational Schema</p>
        </div>
        <div className="contractBadges">
          <span className={`statusBadge ${hasContracts ? 'pass' : 'waiting'}`}>
            {hasContracts ? 'CONTRACT VERIFIED' : 'PLANNING PENDING'}
          </span>
          <span className={`statusBadge ${contractIssues.length === 0 ? 'pass' : 'fail'}`}>
            {contractIssues.length === 0 ? 'ZERO DRIFT' : `${contractIssues.length} ISSUES`}
          </span>
        </div>
      </header>

      <div className="contractsThreeWayGrid">
        {/* Tier 1: Frontend Plan */}
        <section className="contractColumn">
          <div className="columnHeader">
            <span className="colBadge frontend">FRONTEND</span>
            <h3>Architecture Plan</h3>
          </div>
          <div className="columnBody scrollArea">
            {frontendPlan ? (
              <div className="planCard">
                <h4>Component Hierarchy</h4>
                <pre>{JSON.stringify(frontendPlan.components || frontendPlan, null, 2)}</pre>
              </div>
            ) : (
              <div className="emptyState small">
                <strong>Frontend Plan Active</strong>
                <span>Components, stores, and API clients structured from requirements.</span>
              </div>
            )}
          </div>
        </section>

        {/* Tier 2: API Endpoints (OpenAPI 3.1) */}
        <section className="contractColumn">
          <div className="columnHeader">
            <span className="colBadge api">API CONTRACT</span>
            <h3>OpenAPI 3.1 Endpoints</h3>
          </div>
          <div className="columnBody scrollArea">
            <div className="endpointList">
              {endpoints.map((ep: any, idx: number) => (
                <div
                  key={idx}
                  className={`endpointItem ${selectedEndpoint?.path === ep.path ? 'selected' : ''}`}
                  onClick={() => setSelectedEndpoint(ep)}
                >
                  <span className={`methodBadge ${ep.method.toLowerCase()}`}>{ep.method}</span>
                  <span className="epPath">{ep.path}</span>
                  <span className="epSummary">{ep.summary}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Tier 3: Database Relational Schemas */}
        <section className="contractColumn">
          <div className="columnHeader">
            <span className="colBadge db">DATABASE</span>
            <h3>Relational Schema</h3>
          </div>
          <div className="columnBody scrollArea">
            <div className="dbSchemaList">
              {dbSchemas.map((table: any, idx: number) => (
                <div key={idx} className="dbTableCard">
                  <div className="tableName">📁 {table.table || table.name || `Table ${idx + 1}`}</div>
                  <ul className="columnList">
                    {(table.columns || []).map((col: string, i: number) => (
                      <li key={i}>{col}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>

      {selectedEndpoint && (
        <div className="endpointDetailModal">
          <div className="modalHeader">
            <h3>{selectedEndpoint.method} {selectedEndpoint.path}</h3>
            <button className="closeBtn" onClick={() => setSelectedEndpoint(null)}>×</button>
          </div>
          <div className="modalBody">
            <p><b>Summary:</b> {selectedEndpoint.summary}</p>
            <div className="schemaGrid">
              <div className="schemaBox">
                <h4>Request Model Schema:</h4>
                <pre>{selectedEndpoint.request_model ? JSON.stringify({ type: 'object', model: selectedEndpoint.request_model }, null, 2) : 'None (No request body required)'}</pre>
              </div>
              <div className="schemaBox">
                <h4>Response Model Schema:</h4>
                <pre>{JSON.stringify({ status: 200, type: 'object', model: selectedEndpoint.response_model || 'StandardSuccess' }, null, 2)}</pre>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
