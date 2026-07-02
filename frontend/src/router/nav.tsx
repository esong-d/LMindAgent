import type { ReactNode } from 'react'
import {
  HomeOutlined,
  MessageOutlined,
  BookOutlined,
  FolderOutlined,
  CheckSquareOutlined,
  ExperimentOutlined,
  TeamOutlined,
  QuestionCircleOutlined,
  ProfileOutlined,
  PlayCircleOutlined,
  BarChartOutlined,
  EditOutlined,
  SettingOutlined,
} from '@ant-design/icons'

export type NavItem = {
  key: 'overview' | 'chat' | 'knowledge' | 'documents' | 'documentDetail' | 'tasks' | 'evaluation' | 'notes' | 'settings'
  label: string
  path: string
  icon?: ReactNode
  end?: boolean
  children?: Array<{
    key: string
    label: string
    path: string
    icon?: ReactNode
    end?: boolean
  }>
}

export const navItems: NavItem[] = [
  { key: 'overview', label: '总览', path: '/', icon: <HomeOutlined />, end: true },
  { key: 'chat', label: 'Agent 对话', path: '/chat', icon: <MessageOutlined /> },
  { key: 'knowledge', label: '知识库', path: '/knowledge', icon: <BookOutlined /> },
  { key: 'documents', label: '文档管理', path: '/documents', icon: <FolderOutlined />, end: true },
  // { key: 'documentDetail', label: '文档详情', path: '/documents/detail' },
  { key: 'tasks', label: '任务列表', path: '/tasks', icon: <CheckSquareOutlined />, end: true },
  {
    key: 'evaluation',
    label: '测评中心',
    path: '/evaluation',
    icon: <ExperimentOutlined />,
    children: [
      { key: 'evaluation-groups', label: '测评分组', path: '/evaluation/groups', icon: <TeamOutlined />, end: true },
      { key: 'evaluation-questions', label: '测评问题', path: '/evaluation/questions', icon: <QuestionCircleOutlined />, end: true },
      { key: 'evaluation-tasks', label: '测评任务', path: '/evaluation/tasks', icon: <ProfileOutlined />, end: true },
      { key: 'evaluation-runs', label: '测评记录', path: '/evaluation/runs', icon: <PlayCircleOutlined />, end: true },
      { key: 'evaluation-results', label: '测评结果', path: '/evaluation/results', icon: <BarChartOutlined />, end: true },
    ],
  },
  { key: 'notes', label: '笔记', path: '/notes', icon: <EditOutlined /> },
  { key: 'settings', label: '设置', path: '/settings', icon: <SettingOutlined /> },
]
