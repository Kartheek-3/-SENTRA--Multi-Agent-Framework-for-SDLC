export type ProjectSummary = {
  project_id: string;
  project_name: string;
  domain: string;
  workflow_status: string;
  current_agent?: string | null;
};

export type FileNode = {
  name: string;
  path: string;
  type: 'file' | 'directory';
  modified: number;
  size: number;
  children?: FileNode[];
};

export type CreateProjectInput = {
  project_name: string;
  requirement: string;
  scale: string;
  technology_preferences: string[];
  workspace_location?: string;
  github_repository?: string;
  additional_constraints?: string;
};

const API_BASE = import.meta.env.VITE_SEAM_API_URL || 'http://127.0.0.1:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'content-type': 'application/json',
      ...(init?.headers || {}),
    },
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      detail = await response.text();
    }
    throw new Error(detail || `HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const seamApi = {
  baseUrl: API_BASE,
  wsUrl(projectId: string) {
    return `${API_BASE.replace(/^http/, 'ws')}/api/projects/${projectId}/events`;
  },
  health() {
    return request<{ status: string; service: string }>('/health');
  },
  systemHealth() {
    return request<{ backend: string; qwen: string; rag: string; github: string }>('/api/system/health');
  },
  models() {
    return request<any>('/api/system/models');
  },
  listProjects() {
    return request<{ projects: ProjectSummary[] }>('/api/projects');
  },
  createProject(input: CreateProjectInput) {
    return request<{ project_id: string; project_name: string; status: string }>('/api/projects', {
      method: 'POST',
      body: JSON.stringify(input),
    });
  },
  projectStatus(projectId: string) {
    return request<any>(`/api/projects/${projectId}/status`);
  },
  runProject(projectId: string) {
    return request<any>(`/api/projects/${projectId}/run`, { method: 'POST' });
  },
  stopProject(projectId: string) {
    return request<any>(`/api/projects/${projectId}/stop`, { method: 'POST' });
  },
  artifacts(projectId: string) {
    return request<{ artifacts: Array<{ path: string; modified: number; type: string }> }>(`/api/projects/${projectId}/artifacts`);
  },
  diagrams(projectId: string) {
    return request<{ diagrams: string[] }>(`/api/projects/${projectId}/diagrams`);
  },
  diagram(projectId: string, type: string) {
    return request<any>(`/api/projects/${projectId}/diagrams/${encodeURIComponent(type)}`);
  },
  searchKnowledge(query: string, category = '') {
    return request<any>('/api/knowledge/search', {
      method: 'POST',
      body: JSON.stringify({ query, category, top_k: 5 }),
    });
  },
  tree(projectId: string, path = '') {
    return request<{ root: string; path: string; children: FileNode[] }>(
      `/api/projects/${projectId}/filesystem/tree?path=${encodeURIComponent(path)}&depth=5`,
    );
  },
  readFile(projectId: string, path: string) {
    return request<{ path: string; content: string }>(
      `/api/projects/${projectId}/filesystem/file?path=${encodeURIComponent(path)}`,
    );
  },
  fileUrl(projectId: string, path: string) {
    return `${API_BASE}/api/projects/${projectId}/files?path=${encodeURIComponent(path)}`;
  },
  saveFile(projectId: string, path: string, content: string) {
    return request<{ status: string; path: string }>(`/api/projects/${projectId}/filesystem/file`, {
      method: 'PUT',
      body: JSON.stringify({ path, content }),
    });
  },
  createEntry(projectId: string, path: string, type: 'file' | 'directory') {
    return request<any>(`/api/projects/${projectId}/filesystem/entry`, {
      method: 'POST',
      body: JSON.stringify({ path, type }),
    });
  },
  renameEntry(projectId: string, sourcePath: string, targetPath: string) {
    return request<any>(`/api/projects/${projectId}/filesystem/entry`, {
      method: 'PATCH',
      body: JSON.stringify({ source_path: sourcePath, target_path: targetPath }),
    });
  },
  deleteEntry(projectId: string, path: string) {
    return request<any>(`/api/projects/${projectId}/filesystem/entry`, {
      method: 'DELETE',
      body: JSON.stringify({ path }),
    });
  },
};
