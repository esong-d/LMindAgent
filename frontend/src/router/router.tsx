import type { ReactNode } from 'react'
import { Navigate, createBrowserRouter, useLocation } from 'react-router-dom'
import { WorkspaceLayout } from '../layouts/WorkspaceLayout/WorkspaceLayout'
import { ChatPage } from '../pages/ChatPage/ChatPage'
import { DashboardPage } from '../pages/DashboardPage/DashboardPage'
// import { DocumentDetailPage } from '../pages/DocumentDetailPage/DocumentDetailPage'
import { DocumentsPage } from '../pages/DocumentsPage/DocumentsPage'
import { EvaluationPage } from '../pages/EvaluationPage/EvaluationPage'
import { EvaluationGroupsPage } from '../pages/EvaluationPage/EvaluationGroupsPage'
import { EvaluationQuestionsPage } from '../pages/EvaluationPage/EvaluationQuestionsPage'
import { EvaluationResultsPage } from '../pages/EvaluationPage/EvaluationResultsPage'
import { EvaluationRunsPage } from '../pages/EvaluationPage/EvaluationRunsPage'
import { EvaluationTasksPage } from '../pages/EvaluationPage/EvaluationTasksPage'
import { LoginPage } from '../pages/Login/Login'
import { RegisterPage } from '../pages/Login/Register'
import { NotFoundPage } from '../pages/NotFoundPage/NotFoundPage'
import { NotesPage } from '../pages/NotesPage/NotesPage'
import { RouteErrorPage } from '../pages/RouteErrorPage/RouteErrorPage'
import { SettingsPage } from '../pages/SettingsPage/SettingsPage'
import { TaskDetailPage } from '../pages/TaskDetailPage/TaskDetailPage'
import { TasksPage } from '../pages/TasksPage/TasksPage'
import { getAccessToken } from '../features/auth/store'
import { KnowledgePage } from '../pages/Knowledge/Knowledge'

type AppRoute = {
  path: string
  element: ReactNode
}

export const appRoutes: AppRoute[] = [
  { 
    path: '/', 
    element: <DashboardPage />
  },
  { 
    path: '/chat', 
    element: <ChatPage /> 
  },
  { 
    path: '/knowledge', 
    element: <KnowledgePage /> 
  },
  { 
    path: '/documents', 
    element: <DocumentsPage /> 
  },
  {
    path: '/tasks',
    element: <TasksPage />
  },
  // { 
  //   path: '/documents/detail', 
  //   element: <DocumentDetailPage /> 
  // },
  {
    path: '/notes',
    element: <NotesPage />
  },
  { 
    path: '/settings', 
    element: <SettingsPage /> 
  },
  { 
    path: '/tasks/:taskId', 
    element: <TaskDetailPage /> 
  },
]

function RequireAuth({ children }: { children: ReactNode }) {
  const location = useLocation()
  const token = getAccessToken()

  if (!token || token === 'undefined') {
    const from = `${location.pathname}${location.search}`
    return <Navigate to="/login" replace state={{ from }} />
  }

  return children
}

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
    errorElement: <RouteErrorPage />,
  },
  {
    path: '/register',
    element: <RegisterPage />,
    errorElement: <RouteErrorPage />,
  },
  {
    errorElement: <RouteErrorPage />,
    element: (
      <RequireAuth>
        <WorkspaceLayout />
      </RequireAuth>
    ),
    children: [
      { path: 'home', element: <Navigate to="/" replace /> },
      ...appRoutes.map((r) => ({ path: r.path, element: r.element })),
      {
        path: 'evaluation',
        element: <EvaluationPage />,
        children: [
          { index: true, element: <Navigate to="questions" replace /> },
          { path: 'groups', element: <EvaluationGroupsPage /> },
          { path: 'questions', element: <EvaluationQuestionsPage /> },
          { path: 'tasks', element: <EvaluationTasksPage /> },
          { path: 'runs', element: <EvaluationRunsPage /> },
          { path: 'results', element: <EvaluationResultsPage /> },
        ],
      },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
  {
    path: '*',
    element: <NotFoundPage />,
    errorElement: <RouteErrorPage />,
  },
])
