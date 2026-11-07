import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { ProjectBuilder } from '../ProjectBuilder';
import { seamApi } from '../../../api/client';

vi.mock('../../../api/client', () => ({
  seamApi: {
    createProject: vi.fn(),
    runProject: vi.fn(),
    projectStatus: vi.fn(),
    connectGithub: vi.fn(),
  },
}));

describe('ProjectBuilder Component Acceptance Audit', () => {
  const mockOnSelectProject = vi.fn();
  const mockOnOpenWorkspace = vi.fn();
  const mockOnRefreshProjects = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders heading and primary builder interface', () => {
    render(
      <ProjectBuilder
        projects={[]}
        onSelectProject={mockOnSelectProject}
        onOpenWorkspace={mockOnOpenWorkspace}
        onRefreshProjects={mockOnRefreshProjects}
      />
    );

    expect(screen.getByText('Build your next project')).toBeDefined();
    expect(screen.getByPlaceholderText(/Describe the application you want to build/i)).toBeDefined();
    expect(screen.getByText('Generate Project')).toBeDefined();
  });

  it('disables Generate Project button when prompt is empty or under 10 chars', () => {
    render(
      <ProjectBuilder
        projects={[]}
        onSelectProject={mockOnSelectProject}
        onOpenWorkspace={mockOnOpenWorkspace}
      />
    );

    const button = screen.getByText('Generate Project').closest('button');
    expect(button?.disabled).toBe(true);

    const textarea = screen.getByPlaceholderText(/Describe the application you want to build/i);
    fireEvent.change(textarea, { target: { value: 'Too short' } });
    expect(button?.disabled).toBe(true);

    fireEvent.change(textarea, { target: { value: 'This is a sufficiently long valid requirement prompt.' } });
    expect(button?.disabled).toBe(false);
  });

  it('populates prompt and project name when an example chip is clicked', () => {
    render(
      <ProjectBuilder
        projects={[]}
        onSelectProject={mockOnSelectProject}
        onOpenWorkspace={mockOnOpenWorkspace}
      />
    );

    const chip = screen.getByText('Student Association Hub');
    fireEvent.click(chip);

    const textarea = screen.getByPlaceholderText(/Describe the application you want to build/i) as HTMLTextAreaElement;
    expect(textarea.value).toContain('student association management platform');

    // Open advanced configuration to verify project name
    const advToggle = screen.getByText(/Advanced Configuration/i);
    fireEvent.click(advToggle);

    const nameInput = screen.getByPlaceholderText(/auto-derived if empty/i) as HTMLInputElement;
    expect(nameInput.value).toBe('student-association-platform');
  });

  it('switches technology stack presets', () => {
    render(
      <ProjectBuilder
        projects={[]}
        onSelectProject={mockOnSelectProject}
        onOpenWorkspace={mockOnOpenWorkspace}
      />
    );

    const pythonPreset = screen.getByText('Python Cloud API');
    fireEvent.click(pythonPreset);

    // Verify preset is selected
    expect(pythonPreset.closest('.presetCard')?.classList.contains('selected')).toBe(true);
  });

  it('toggles custom stack configuration and advanced options', () => {
    render(
      <ProjectBuilder
        projects={[]}
        onSelectProject={mockOnSelectProject}
        onOpenWorkspace={mockOnOpenWorkspace}
      />
    );

    // Custom stack
    const customToggle = screen.getByText(/Customize Stack Details/i);
    fireEvent.click(customToggle);
    expect(screen.getByText('Language')).toBeDefined();
    expect(screen.getByText('Frontend Framework')).toBeDefined();
    expect(screen.getByText('Backend Framework')).toBeDefined();

    // Advanced options
    const advToggle = screen.getByText(/Advanced Configuration/i);
    fireEvent.click(advToggle);
    expect(screen.getByText('Estimated Project Scale')).toBeDefined();
    expect(screen.getByText('Project Name (Optional)')).toBeDefined();
  });

  it('submits project generation with selected stack configuration', async () => {
    (seamApi.createProject as any).mockResolvedValue({
      project_id: 'test-gen-id-123',
      project_name: 'test-proj',
      status: 'created',
    });
    (seamApi.runProject as any).mockResolvedValue({
      project_id: 'test-gen-id-123',
      status: 'running',
    });
    (seamApi.projectStatus as any).mockResolvedValue({
      project_id: 'test-gen-id-123',
      workflow_status: 'completed',
      current_agent: 'DeliveryAgent',
      delivery_result: { status: 'packaged' },
    });

    render(
      <ProjectBuilder
        projects={[]}
        onSelectProject={mockOnSelectProject}
        onOpenWorkspace={mockOnOpenWorkspace}
        onRefreshProjects={mockOnRefreshProjects}
      />
    );

    const textarea = screen.getByPlaceholderText(/Describe the application you want to build/i);
    fireEvent.change(textarea, { target: { value: 'Build an end-to-end task tracker with priority ordering and tags.' } });

    const submitBtn = screen.getByText('Generate Project');
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(seamApi.createProject).toHaveBeenCalledTimes(1);
    });

    expect(seamApi.createProject).toHaveBeenCalledWith(
      expect.objectContaining({
        requirement: 'Build an end-to-end task tracker with priority ordering and tags.',
        workflow_type: 'new_project',
        technology_stack: expect.any(Object),
      })
    );
  });

  it('switches to Workflow B for GitHub enhancement and displays approval gate warning', () => {
    render(
      <ProjectBuilder
        projects={[]}
        onSelectProject={mockOnSelectProject}
        onOpenWorkspace={mockOnOpenWorkspace}
      />
    );

    const workflowBBtn = screen.getByText(/Enhance Existing Repo \(GitHub\)/i);
    fireEvent.click(workflowBBtn);

    expect(screen.getByText(/GitHub Repository URL or Slug/i)).toBeDefined();
    expect(screen.getByText(/SEAM Approval Gate Enforced/i)).toBeDefined();
    expect(screen.getByText(/No files will be modified or committed without your explicit approval/i)).toBeDefined();
  });
});
