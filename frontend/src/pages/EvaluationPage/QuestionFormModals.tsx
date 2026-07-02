import { useEffect, useMemo, useState } from 'react'
import { Form, Input, InputNumber, Modal, Select } from 'antd'
import { listAllDocuments } from '../../features/documents/api'
import type { DocumentItem } from '../../features/documents/types'
import { listAllEvaluationGroups } from '../../features/evaluation/api'
import type { EvaluationGroupOption, EvaluationQuestion } from '../../features/evaluation/types'
import { listAllKnowledgeBaseItems } from '../../features/knowledge-bases/api'
import type { KnowledgeBaseItem } from '../../features/knowledge-bases/types'
import { listAllModelConfigs } from '../../features/settings/api'
import type { ModelConfigOut } from '../../features/settings/types'
import { questionSourceOptions } from './evaluationShared'

export type QuestionFormValues = {
  group_id: string
  question?: string
  expected_answer?: string
  source: string
  chunk_ids_text?: string
  knowledge_base_id?: string
  document_id?: string
  model_config_id?: string
  question_count?: number
}

type CreateQuestionModalProps = {
  open: boolean
  confirmLoading: boolean
  onCancel: () => void
  onSubmit: (values: QuestionFormValues) => Promise<void> | void
}

type EditQuestionModalProps = {
  open: boolean
  confirmLoading: boolean
  question: EvaluationQuestion | null
  onCancel: () => void
  onSubmit: (values: QuestionFormValues) => Promise<void> | void
  onAfterClose?: () => void
}

function selectLabelFilter(input: string, option?: { label?: unknown }) {
  return String(option?.label ?? '')
    .toLowerCase()
    .includes(input.trim().toLowerCase())
}

export function CreateQuestionModal({ open, confirmLoading, onCancel, onSubmit }: CreateQuestionModalProps) {
  const [form] = Form.useForm<QuestionFormValues>()
  const [groups, setGroups] = useState<EvaluationGroupOption[]>([])
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBaseItem[]>([])
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [modelConfigs, setModelConfigs] = useState<ModelConfigOut[]>([])
  const [groupsLoading, setGroupsLoading] = useState(false)
  const [knowledgeBasesLoading, setKnowledgeBasesLoading] = useState(false)
  const [documentsLoading, setDocumentsLoading] = useState(false)
  const [modelConfigsLoading, setModelConfigsLoading] = useState(false)
  const source = Form.useWatch('source', form) ?? 'ai'
  const knowledgeBaseId = Form.useWatch('knowledge_base_id', form)
  const documentOptions = useMemo(
    () =>
      documents.map((item) => ({
        label: item.original_filename || item.filename || item.id,
        value: item.id,
      })),
    [documents],
  )
  const modelConfigOptions = useMemo(
    () =>
      modelConfigs.map((item) => ({
        label: item.provider ? `${item.name || item.id} (${item.provider})` : item.name || item.id,
        value: item.id,
      })),
    [modelConfigs],
  )

  useEffect(() => {
    if (!open) return
    form.setFieldsValue({
      group_id: '',
      question: '',
      expected_answer: '',
      source: 'ai',
      chunk_ids_text: '',
      knowledge_base_id: '',
      document_id: '',
      model_config_id: '',
      question_count: 1,
    })
  }, [form, open])

  useEffect(() => {
    if (!open) return

    let cancelled = false
    async function loadGroups() {
      setGroupsLoading(true)
      try {
        const groupList = await listAllEvaluationGroups()
        if (cancelled) return
        setGroups(groupList)
      } finally {
        if (!cancelled) setGroupsLoading(false)
      }
    }

    void loadGroups()

    return () => {
      cancelled = true
    }
  }, [open])

  useEffect(() => {
    if (!open) return

    let cancelled = false
    async function loadModelConfigs() {
      setModelConfigsLoading(true)
      try {
        const modelConfigList = await listAllModelConfigs()
        if (cancelled) return
        setModelConfigs(modelConfigList)
      } finally {
        if (!cancelled) setModelConfigsLoading(false)
      }
    }

    void loadModelConfigs()

    return () => {
      cancelled = true
    }
  }, [open])

  useEffect(() => {
    if (!open) return

    let cancelled = false
    async function loadKnowledgeBases() {
      setKnowledgeBasesLoading(true)
      try {
        const knowledgeBaseList = await listAllKnowledgeBaseItems()
        if (cancelled) return
        setKnowledgeBases(knowledgeBaseList)
      } finally {
        if (!cancelled) setKnowledgeBasesLoading(false)
      }
    }

    void loadKnowledgeBases()

    return () => {
      cancelled = true
    }
  }, [open])

  useEffect(() => {
    if (!open) return
    form.setFieldValue('document_id', '')

    if (!knowledgeBaseId) {
      setDocuments([])
      return
    }

    let cancelled = false
    async function loadDocuments() {
      setDocumentsLoading(true)
      try {
        const nextDocuments = await listAllDocuments({ knowledge_base_id: knowledgeBaseId })
        if (cancelled) return
        setDocuments(nextDocuments)
      } finally {
        if (!cancelled) setDocumentsLoading(false)
      }
    }

    void loadDocuments()

    return () => {
      cancelled = true
    }
  }, [form, knowledgeBaseId, open])

  return (
    <Modal
      title="新建测评问题"
      open={open}
      onCancel={onCancel}
      onOk={async () => {
        const values = await form.validateFields()
        await onSubmit(values)
      }}
      okText="保存"
      cancelText="取消"
      confirmLoading={confirmLoading}
      afterClose={() => form.resetFields()}
    >
      <Form form={form} layout="vertical" preserve={false} requiredMark={false}>
        <Form.Item name="group_id" label="所属分组" rules={[{ required: true, message: '请选择所属分组' }]}>
          <Select
            placeholder="请选择所属分组"
            loading={groupsLoading}
            showSearch
            filterOption={selectLabelFilter}
            options={groups.map((item) => ({ label: item.name, value: item.id }))}
          />
        </Form.Item>
        <Form.Item name="source" label="来源" initialValue="ai">
          <Select options={questionSourceOptions} />
        </Form.Item>
        {source === 'ai' ? (
          <>
            <Form.Item
              name="knowledge_base_id"
              label="知识库"
              rules={[{ required: true, message: '请选择知识库' }]}
            >
              <Select
                placeholder="请选择知识库"
                loading={knowledgeBasesLoading}
                options={knowledgeBases.map((item) => ({ label: item.name, value: item.id }))}
              />
            </Form.Item>
            <Form.Item
              name="document_id"
              label="文档"
              rules={[{ required: true, message: '请选择文档' }]}
            >
              <Select
                placeholder={knowledgeBaseId ? '请选择文档' : '请先选择知识库'}
                loading={documentsLoading}
                disabled={!knowledgeBaseId}
                showSearch
                filterOption={selectLabelFilter}
                options={documentOptions}
              />
            </Form.Item>
            <Form.Item
              name="model_config_id"
              label="模型配置"
              rules={[{ required: true, message: '请选择模型配置' }]}
            >
              <Select
                placeholder="请选择模型配置"
                loading={modelConfigsLoading}
                showSearch
                filterOption={selectLabelFilter}
                options={modelConfigOptions}
              />
            </Form.Item>
            <Form.Item
              name="question_count"
              label="生成问题数"
              rules={[
                { required: true, message: '请输入生成问题数' },
                { type: 'number', min: 1, message: '生成问题数至少为 1' },
              ]}
            >
              <InputNumber min={1} precision={0} style={{ width: '100%' }} placeholder="请输入要生成的问题数量" />
            </Form.Item>
          </>
        ) : (
          <>
            <Form.Item name="question" label="问题内容" rules={[{ required: true, message: '请填写测评问题' }]}>
              <Input.TextArea rows={4} placeholder="请输入测评问题" maxLength={2000} showCount />
            </Form.Item>
            <Form.Item name="expected_answer" label="期望答案">
              <Input.TextArea rows={4} placeholder="可选" />
            </Form.Item>
            <Form.Item name="chunk_ids_text" label="关联 Chunk IDs">
              <Input.TextArea rows={3} placeholder="多个 ID 可用换行或逗号分隔" />
            </Form.Item>
          </>
        )}
      </Form>
    </Modal>
  )
}

export function EditQuestionModal({ open, confirmLoading, question, onCancel, onSubmit, onAfterClose }: EditQuestionModalProps) {
  const [form] = Form.useForm<QuestionFormValues>()
  const [groups, setGroups] = useState<EvaluationGroupOption[]>([])
  const [groupsLoading, setGroupsLoading] = useState(false)

  useEffect(() => {
    if (!open) return

    let cancelled = false
    async function loadGroups() {
      setGroupsLoading(true)
      try {
        const groupList = await listAllEvaluationGroups()
        if (cancelled) return
        setGroups(groupList)
      } finally {
        if (!cancelled) setGroupsLoading(false)
      }
    }

    void loadGroups()

    return () => {
      cancelled = true
    }
  }, [open])

  useEffect(() => {
    if (!open) return
    if (!question) {
      form.resetFields()
      return
    }
    form.setFieldsValue({
      group_id: question.group?.id ?? '',
      question: question.question,
      expected_answer: question.expected_answer ?? '',
      source: question.source || 'human',
    })
  }, [form, open, question])

  return (
    <Modal
      title="编辑测评问题"
      open={open}
      forceRender
      onCancel={onCancel}
      onOk={async () => {
        const values = await form.validateFields()
        await onSubmit(values)
      }}
      okText="保存"
      cancelText="取消"
      confirmLoading={confirmLoading}
      afterClose={() => {
        form.resetFields()
        onAfterClose?.()
      }}
    >
      <Form form={form} layout="vertical" preserve={false} requiredMark={false}>
        <Form.Item name="group_id" label="所属分组" rules={[{ required: true, message: '请选择所属分组' }]}>
          <Select
            placeholder="请选择所属分组"
            loading={groupsLoading}
            showSearch
            filterOption={selectLabelFilter}
            options={groups.map((item) => ({ label: item.name, value: item.id }))}
          />
        </Form.Item>
        <Form.Item name="source" label="来源" initialValue="human">
          <Select options={questionSourceOptions} />
        </Form.Item>
        <Form.Item name="question" label="问题内容" rules={[{ required: true, message: '请填写测评问题' }]}>
          <Input.TextArea rows={4} placeholder="请输入测评问题" maxLength={2000} showCount />
        </Form.Item>
        <Form.Item name="expected_answer" label="期望答案">
          <Input.TextArea rows={8} placeholder="可选" />
        </Form.Item>
      </Form>
    </Modal>
  )
}
