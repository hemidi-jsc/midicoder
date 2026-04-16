/**
 * Cấu hình routing cho ứng dụng
 */

import { Routes } from '@angular/router';

// Guards
import { AuthGuard } from './core/auth.guard';

export const routes: Routes = [
  // Route login (không cần auth)
  {
    path: 'login',
    loadComponent: () => import('./pages/login/login.component').then((m) => m.LoginComponent),
  },

  // Routes yêu cầu authentication
  {
    path: '',
    canActivate: [AuthGuard],
    children: [
      // Dashboard là route mặc định
      {
        path: '',
        redirectTo: 'dashboard',
        pathMatch: 'full',
      },
      {
        path: 'dashboard',
        loadComponent: () => import('./pages/dashboard/dashboard.component').then((m) => m.DashboardComponent),
      },
      {
        path: 'brief-editor',
        loadComponent: () => import('./pages/brief-editor/brief-editor.component').then((m) => m.BriefEditorComponent),
      },
      {
        path: 'clarification',
        loadComponent: () => import('./pages/clarification/clarification.component').then((m) => m.ClarificationComponent),
      },
      {
        path: 'contract-viewer',
        loadComponent: () => import('./pages/contract-viewer/contract-viewer.component').then((m) => m.ContractViewerComponent),
      },
      {
        path: 'ir-explorer',
        loadComponent: () => import('./pages/ir-explorer/ir-explorer.component').then((m) => m.IRExplorerComponent),
      },
      {
        path: 'code-generator',
        loadComponent: () => import('./pages/code-generator/code-generator.component').then((m) => m.CodeGeneratorComponent),
      },
      {
        path: 'preview',
        loadComponent: () => import('./pages/preview/preview.component').then((m) => m.PreviewComponent),
      },
      {
        path: 'feedback',
        loadComponent: () => import('./pages/feedback/feedback.component').then((m) => m.FeedbackComponent),
      },
    ],
  },

  // Catch all route
  {
    path: '**',
    redirectTo: 'login',
  },
];