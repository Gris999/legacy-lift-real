/** View state shared by pipeline presentation and the workspace facade. */
export interface StageView {
  id: string;
  label: string;
  description: string;
  sprint: string;
  index: string;
  status: 'locked' | 'ready' | 'running' | 'completed' | 'failed';
}
