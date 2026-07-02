import styles from './SettingsPage.module.css'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Badge, Button, Card, Form, Input, List, Modal, Popconfirm, Select, Space, Tag, Typography } from 'antd'
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons'
import { useToast } from '../../components/Toast/ToastProvider'
import { ApiError } from '../../lib/apiClient'
import { formatMonthDayTimeWithSecond } from '../../lib/dateTime'
import { createModelConfig, deleteModelConfig, getModelConfig, listModelConfigs, setDefaultModelConfig, testModelConfig, updateModelConfig } from '../../features/settings/api'
import { getStoredSelectedModelConfigId, setStoredSelectedModelConfigId } from '../../features/settings/store'
import type { CreateModelConfigBody, ModelConfigOut, UpdateModelConfigBody } from '../../features/settings/types'

function selectLabelFilter(input: string, option?: { label?: unknown }) {
  return String(option?.label ?? '')
    .toLowerCase()
    .includes(input.trim().toLowerCase())
}

export function SettingsPage() {
  const { showToast } = useToast()

  const [configs, setConfigs] = useState<ModelConfigOut[]>([])
  const [listLoading, setListLoading] = useState(false)
  const [activeId, setActiveId] = useState<string | null>(null)
  const [activeConfig, setActiveConfig] = useState<ModelConfigOut | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [settingDefault, setSettingDefault] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [search, setSearch] = useState('')
  const [createOpen, setCreateOpen] = useState(false)
  const [createSaving, setCreateSaving] = useState(false)

  type ModelConfigFormValues = {
    name: string
    provider: string
    mode: string
    base_url: string
    api_key?: string
    chat_model: string
    embedding_model: string
    data_policy: string
    is_default: boolean
  }

  const [form] = Form.useForm<ModelConfigFormValues>()
  const modeValue = Form.useWatch('mode', form) ?? 'all'
  const providerValue = Form.useWatch('provider', form) ?? ''
  const chatModelRequired = modeValue !== 'embedding'

  const [createForm] = Form.useForm<ModelConfigFormValues>()
  const createModeValue = Form.useWatch('mode', createForm) ?? 'all'
  const createProviderValue = Form.useWatch('provider', createForm) ?? ''
  const createChatModelRequired = createModeValue !== 'embedding'

  const mapConfigToFormValues = useCallback((config: ModelConfigOut): ModelConfigFormValues => ({
    name: config.name ?? '',
    provider: config.provider ?? '',
    mode: config.mode ?? '',
    base_url: (config.base_url ?? '').trim(),
    api_key: config.api_key_masked ?? '',
    chat_model: config.chat_model ?? '',
    embedding_model: config.embedding_model ?? '',
    data_policy: config.data_policy ?? '',
    is_default: !!config.is_default,
  }), [])

  const normalizeErrorMessage = useCallback((err: unknown) => {
    if (err instanceof ApiError) return err.message || '请求失败'
    if (err instanceof Error) return err.message || '请求失败'
    return '请求失败'
  }, [])

  const statusTag = useCallback((status: string) => {
    if (status === 'available') return <Tag color="green">成功</Tag>
    if (status === 'failed') return <Tag color="red">失败</Tag>
    if (status === 'untested') return <Tag>未测试</Tag>
    return <Tag>{status || '未知'}</Tag>
  }, [])

  const providerItems = useMemo(() => [
    {
      name: '云模型 API',
      value: 'openai',
      description: '使用 OpenAI、Anthropic、Google、Azure 等托管模型',
    },
    {
      name: '本地模型',
      value: 'ollama',
      description: '连接 Ollama、LM Studio 或本地推理服务',
    },
    {
      name: '私有部署',
      value: 'custom',
      description: '连接兼容 OpenAI 协议的内网模型或代理服务',
    },
  ], [])

  // 云模型支持的厂商
  const cloudProviders = useMemo(() => ['openai', 'anthropic', 'deepseek', 'ollama'], [])
  const cloudProviderOptions = useMemo(() => cloudProviders.map((p) => ({ label: p, value: p })), [cloudProviders])
  // 云模型支持的聊天模型
  const chatModelMap = useMemo<Record<string, string[]>>(
    () => ({
      openai: ['gpt-4.1-mini', 'gpt-5.1', 'gpt-5.2', 'gpt-5.4'],
      anthropic: ['claude-sonnet-4-0', 'claude-opus-4-0'],
      deepseek: ['deepseek-v4-pro', 'deepseek-v4-flash'],
      ollama: ['qwen3:8b', 'llama3.1:8b', 'deepseek-v3.1'],
    }),
    [],
  )
  const chatModelOptions = useMemo(
    () => (chatModelMap[providerValue] ?? []).map((p) => ({ label: p, value: p })),
    [chatModelMap, providerValue],
  )
  const createChatModelOptions = useMemo(
    () => (chatModelMap[createProviderValue] ?? []).map((p) => ({ label: p, value: p })),
    [chatModelMap, createProviderValue],
  )

  const resolveProviderGroup = useCallback((provider: string | undefined | null) => {
    const normalized = String(provider ?? '').trim().toLowerCase()
    if (!normalized) return ''
    if (['openai', 'anthropic', 'google', 'azure'].includes(normalized)) return 'openai'
    if (normalized.includes('ollama') || normalized.includes('lmstudio') || normalized.includes('lm-studio')) return 'ollama'
    if (normalized === 'custom') return 'custom'
    return 'custom'
  }, [])

  const renderProviderPicker = useCallback(
    (currentProvider: string | undefined, onPick: (provider: string) => void) => {
      const activeGroup = resolveProviderGroup(currentProvider)

      return (
        <div className={styles.providerSection}>
          <div className={styles.providerTabs}>
            {providerItems.map((item) => {
              const active = item.value === activeGroup
              return (
                <button
                  key={item.value}
                  type="button"
                  className={active ? styles.providerTabActive : styles.providerTab}
                  onClick={() => onPick(item.value)}
                >
                  <span className={styles.providerTabTitle}>{item.name}</span>
                  <span className={styles.providerTabDesc}>{item.description}</span>
                </button>
              )
            })}
          </div>
        </div>
      )
    },
    [providerItems, resolveProviderGroup],
  )

  const filteredConfigs = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return configs
    return configs.filter((c) => {
      const haystack = `${c.name} ${c.provider} ${c.chat_model} ${c.embedding_model} ${c.base_url}`.toLowerCase()
      return haystack.includes(q)
    })
  }, [configs, search])

  const pickInitialActiveId = useCallback((items: ModelConfigOut[]) => {
    const stored = getStoredSelectedModelConfigId()
    if (stored && items.some((c) => c.id === stored)) return stored
    const def = items.find((c) => c.is_default)
    if (def) return def.id
    return items[0]?.id ?? null
  }, [])

  const openCreate = useCallback(() => {
    createForm.setFieldsValue({
      name: '',
      provider: 'openai',
      mode: 'all',
      base_url: 'https://api.openai.com/v1',
      api_key: '',
      chat_model: 'gpt-4.1-mini',
      embedding_model: 'text-embedding-3-small',
      data_policy: 'chunks_only',
      is_default: false,
    })
    setCreateOpen(true)
  }, [createForm])

  const reloadList = useCallback(
    async (opts?: { keepActive?: boolean; preferredActiveId?: string | null }) => {
      setListLoading(true)
      try {
        const items = await listModelConfigs()
        setConfigs(items)
        setActiveId((currentActiveId) => {
          if (opts?.preferredActiveId && items.some((c) => c.id === opts.preferredActiveId)) return opts.preferredActiveId
          if (opts?.keepActive && currentActiveId && items.some((c) => c.id === currentActiveId)) return currentActiveId
          return pickInitialActiveId(items)
        })
      } catch (err) {
        const message = normalizeErrorMessage(err)
        showToast({ type: 'error', title: '加载模型配置失败', message })
      } finally {
        setListLoading(false)
      }
    },
    [normalizeErrorMessage, pickInitialActiveId, showToast],
  )

  const loadDetail = useCallback(
    async (id: string) => {
      setDetailLoading(true)
      try {
        const data = await getModelConfig(id)
        setActiveConfig(data)
        setStoredSelectedModelConfigId(id)
      } catch (err) {
        const message = normalizeErrorMessage(err)
        showToast({ type: 'error', title: '加载模型配置详情失败', message })
        setActiveId(null)
        setActiveConfig(null)
        setStoredSelectedModelConfigId(null)
      } finally {
        setDetailLoading(false)
      }
    },
    [normalizeErrorMessage, showToast],
  )

  useEffect(() => {
    reloadList().catch(() => {})
  }, [reloadList])

  useEffect(() => {
    if (!activeId) return
    loadDetail(activeId).catch(() => {})
  }, [activeId, loadDetail])

  useEffect(() => {
    if (!activeConfig) {
      form.resetFields()
      return
    }

    form.resetFields()
    form.setFieldsValue(mapConfigToFormValues(activeConfig))
  }, [activeConfig, form, mapConfigToFormValues])

  const submitSave = useCallback(async () => {
    if (!activeId) return

    const values = await form.validateFields()

    const normalizedBaseUrl = values.base_url?.trim() ?? ''
    const normalizedName = values.name?.trim() ?? ''
    const normalizedProvider = values.provider?.trim() ?? ''
    const normalizedMode = values.mode?.trim() ?? ''
    const normalizedChatModel = values.chat_model?.trim() ?? ''
    const normalizedEmbeddingModel = values.embedding_model?.trim() ?? ''
    const normalizedDataPolicy = values.data_policy?.trim() ?? 'chunks_only'
    const apiKey = (values.api_key ?? '').trim()
    const currentMaskedApiKey = (activeConfig?.api_key_masked ?? '').trim()
    const isDefault = !!values.is_default

    if (!normalizedName || !normalizedProvider || !normalizedBaseUrl) {
      console.log(values)
      showToast({ type: 'warn', title: '请完善必填信息', message: '名称 / 提供方 / Base URL 不能为空。' })
      return
    }

    const needChat = normalizedMode !== 'embedding'
    if (needChat && !normalizedChatModel) {
      showToast({ type: 'warn', title: '缺少对话模型', message: '当前模式需要填写对话模型（chat_model）。' })
      return
    }

    setSaving(true)
    try {
      const body: UpdateModelConfigBody = {
        name: normalizedName,
        provider: normalizedProvider,
        mode: normalizedMode,
        base_url: normalizedBaseUrl,
        chat_model: normalizedChatModel,
        embedding_model: normalizedEmbeddingModel,
        data_policy: normalizedDataPolicy,
        is_default: isDefault,
      }
      if (apiKey && apiKey !== currentMaskedApiKey) body.api_key = apiKey

      const updated = await updateModelConfig(activeId, body)
      showToast({ type: 'success', title: '已保存', message: updated.name })
      await reloadList({ keepActive: true })

      const shouldSetDefault = isDefault && !activeConfig?.is_default
      if (shouldSetDefault) {
        setSettingDefault(true)
        try {
          await setDefaultModelConfig(activeId)
          showToast({ type: 'success', title: '默认配置已更新', message: updated.name })
        } finally {
          setSettingDefault(false)
        }
        await reloadList({ keepActive: true })
      }
    } catch (err) {
      const message = normalizeErrorMessage(err)
      showToast({ type: 'error', title: '保存失败', message })
    } finally {
      setSaving(false)
    }
  }, [activeConfig?.api_key_masked, activeConfig?.is_default, activeId, form, normalizeErrorMessage, reloadList, showToast])

  const submitCreate = useCallback(async () => {
    const values = await createForm.validateFields()

    const normalizedBaseUrl = values.base_url?.trim() ?? ''
    const normalizedName = values.name?.trim() ?? ''
    const normalizedProvider = values.provider?.trim() ?? ''
    const normalizedMode = values.mode?.trim() ?? ''
    const normalizedChatModel = values.chat_model?.trim() ?? ''
    const normalizedEmbeddingModel = values.embedding_model?.trim() ?? ''
    const normalizedDataPolicy = values.data_policy?.trim() ?? 'chunks_only'
    const apiKey = (values.api_key ?? '').trim()
    const isDefault = !!values.is_default

    if (!normalizedName || !normalizedProvider || !normalizedBaseUrl) {
      console.log(values)
      showToast({ type: 'warn', title: '请完善必填信息', message: '名称 / 提供方 / Base URL 不能为空。' })
      return
    }
    if (!apiKey) {
      showToast({ type: 'warn', title: '缺少 API Key', message: '创建新配置需要填写 API Key。' })
      return
    }

    const needChat = normalizedMode !== 'embedding'
    if (needChat && !normalizedChatModel) {
      showToast({ type: 'warn', title: '缺少对话模型', message: '当前模式需要填写对话模型（chat_model）。' })
      return
    }

    setCreateSaving(true)
    try {
      const body: CreateModelConfigBody = {
        name: normalizedName,
        provider: normalizedProvider,
        mode: normalizedMode,
        base_url: normalizedBaseUrl,
        api_key: apiKey,
        chat_model: normalizedChatModel,
        embedding_model: normalizedEmbeddingModel,
        data_policy: normalizedDataPolicy,
        is_default: isDefault,
      }
      const created = await createModelConfig(body)
      showToast({ type: 'success', title: '创建成功', message: created.name })
      setCreateOpen(false)
      createForm.resetFields()
      setStoredSelectedModelConfigId(created.id)
      await reloadList({ preferredActiveId: created.id })

      if (isDefault) {
        setSettingDefault(true)
        try {
          await setDefaultModelConfig(created.id)
        } finally {
          setSettingDefault(false)
        }
        await reloadList({ keepActive: true, preferredActiveId: created.id })
      }
    } catch (err) {
      const message = normalizeErrorMessage(err)
      showToast({ type: 'error', title: '创建失败', message })
    } finally {
      setCreateSaving(false)
    }
  }, [createForm, normalizeErrorMessage, reloadList, showToast])

  const submitTest = useCallback(async () => {
    if (!activeId) return
    setTesting(true)
    try {
      await testModelConfig(activeId)
      showToast({ type: 'success', title: '测试已触发', message: '请稍后查看状态更新。' })
      await reloadList({ keepActive: true })
      await loadDetail(activeId)
    } catch (err) {
      const message = normalizeErrorMessage(err)
      showToast({ type: 'error', title: '测试失败', message })
    } finally {
      setTesting(false)
    }
  }, [activeId, loadDetail, normalizeErrorMessage, reloadList, showToast])

  const submitSetDefault = useCallback(async () => {
    if (!activeId) return
    setSettingDefault(true)
    try {
      await setDefaultModelConfig(activeId)
      showToast({ type: 'success', title: '已设为默认', message: activeConfig?.name ?? '' })
      await reloadList({ keepActive: true })
      await loadDetail(activeId)
    } catch (err) {
      const message = normalizeErrorMessage(err)
      showToast({ type: 'error', title: '设置默认失败', message })
    } finally {
      setSettingDefault(false)
    }
  }, [activeConfig?.name, activeId, loadDetail, normalizeErrorMessage, reloadList, showToast])

  const submitDelete = useCallback(async () => {
    if (!activeId) return
    setDeleting(true)
    try {
      await deleteModelConfig(activeId)
      showToast({ type: 'success', title: '已删除', message: activeConfig?.name ?? '' })
      setActiveId(null)
      setActiveConfig(null)
      setStoredSelectedModelConfigId(null)
      await reloadList()
    } catch (err) {
      const message = normalizeErrorMessage(err)
      showToast({ type: 'error', title: '删除失败', message })
    } finally {
      setDeleting(false)
    }
  }, [activeConfig?.name, activeId, normalizeErrorMessage, reloadList, showToast])

  const detailTitle = activeId ? activeConfig?.name || '模型配置' : '模型配置'

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <h1 className={styles.title}>模型配置</h1>
          <Typography.Text type="secondary">管理多个模型提供方配置，支持测试与默认切换。</Typography.Text>
        </div>
        <Space wrap>
          <Button icon={<ReloadOutlined />} loading={listLoading} onClick={() => reloadList({ keepActive: true })}>
            刷新
          </Button>
            <Button icon={<PlusOutlined />} type="primary" onClick={openCreate}>
            新增配置
          </Button>
        </Space>
      </div>

      <div className={styles.grid}>
        <Card className={styles.sidebarCard} bodyStyle={{ padding: 12 }} variant="outlined">
          <div className={styles.sidebarHeader}>
            <Input.Search placeholder="搜索名称 / Provider / Model" allowClear value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          <List
            loading={listLoading}
            dataSource={filteredConfigs}
            locale={{ emptyText: '暂无模型配置，点击右上角新增。' }}
            renderItem={(item) => {
              const isActive = item.id === activeId
              const title = (
                <Space size={8} align="center" wrap>
                  <Typography.Text strong>{item.name || '未命名'}</Typography.Text>
                  {item.is_default ? <Badge color="blue" text="默认" /> : null}
                </Space>
              )

              const desc = (
                <Space size={6} wrap>
                  <Tag>{item.provider || 'provider'}</Tag>
                  {statusTag(item.status)}
                </Space>
              )

              return (
                <List.Item
                  className={isActive ? styles.listItemActive : styles.listItem}
                  onClick={() => {
                    setActiveId(item.id)
                    setStoredSelectedModelConfigId(item.id)
                  }}
                >
                  <List.Item.Meta title={title} description={desc} />
                </List.Item>
              )
            }}
          />
        </Card>

        <Card
          className={styles.contentCard}
          variant="outlined"
          title={detailTitle}
          loading={detailLoading}
          extra={
            <Space wrap>
              {activeId ? (
                <>
                  <Button loading={testing} onClick={submitTest}>
                    测试连接
                  </Button>
                  <Button disabled={!!activeConfig?.is_default} loading={settingDefault} onClick={submitSetDefault}>
                    设为默认
                  </Button>
                  <Popconfirm
                    title="确定删除这个配置吗？"
                    description={activeConfig?.name ? `将删除「${activeConfig.name}」` : '该操作不可恢复'}
                    okText="删除"
                    cancelText="取消"
                    okButtonProps={{ danger: true }}
                    onConfirm={submitDelete}
                    disabled={deleting || saving || detailLoading}
                  >
                    <Button danger loading={deleting}>
                      删除
                    </Button>
                  </Popconfirm>
                </>
              ) : null}
              <Button type="primary" loading={saving} onClick={submitSave}>
                保存
              </Button>
            </Space>
          }
        >
          {activeId
            ? renderProviderPicker(providerValue, (provider) => {
                form.setFieldValue('provider', provider)
              })
            : null}

          {activeId ? (
            <Form form={form} layout="vertical" className={styles.form}>
              <div className={styles.formGrid}>
                <Form.Item label="名称" name="name" rules={[{ required: true, message: '请输入名称' }]}>
                  <Input placeholder="例如: OpenAI / Azure / 本地 Ollama" />
                </Form.Item>

                <Form.Item label="提供方" name="provider" rules={[{ required: true, message: '请选择提供方' }]}>
                  <Select
                    showSearch
                    options={cloudProviderOptions}
                    placeholder="请选择提供方"
                    filterOption={selectLabelFilter}
                  />
                </Form.Item>

                <Form.Item label="Base URL" name="base_url" rules={[{ required: true, message: '请输入 Base URL' }]}>
                  <Input placeholder="例如：https://api.openai.com/v1" />
                </Form.Item>

                <Form.Item
                  label="对话模型"
                  name="chat_model"
                  rules={[
                    {
                      validator: async (_, value) => {
                        if (!chatModelRequired) return
                        const v = String(value ?? '').trim()
                        if (!v) throw new Error('请输入对话模型')
                      },
                    },
                  ]}
                >
                  <Select
                    showSearch
                    options={chatModelOptions}
                    placeholder="请选择对话模型"
                    filterOption={selectLabelFilter}
                  />
                </Form.Item>

                <Form.Item
                  label="API Key"
                  name="api_key"
                  extra={
                    activeId ? (
                      <div className={styles.apiKeyMeta}>
                        <Space size={[8, 8]} wrap>
                          <span className={styles.apiKeyMetaItem}>
                            <span className={styles.apiKeyHint}>留空表示不更新</span>
                          </span>
                          <span className={styles.apiKeyMetaItem}>
                            <span className={styles.apiKeyMetaLabel}>状态</span>
                            {statusTag(activeConfig?.status ?? '')}
                          </span>
                          <span className={styles.apiKeyMetaItem}>
                            <span className={styles.apiKeyMetaLabel}>上次测试</span>
                            <span>{activeConfig?.last_tested_at ? formatMonthDayTimeWithSecond(activeConfig.last_tested_at) : '—'}</span>
                          </span>
                        </Space>
                      </div>
                    ) : undefined
                  }
                >
                  <Input.Password placeholder="留空表示不更新" autoComplete="new-password" />
                </Form.Item>
              </div>
            </Form>
          ) : (
            <div className={styles.emptyDetail}>
              <Typography.Text type="secondary">还没有模型配置，点击右上角“新增配置”开始创建。</Typography.Text>
            </div>
          )}
        </Card>
      </div>

      <Modal
        title="新增模型配置"
        open={createOpen}
        onCancel={() => {
          setCreateOpen(false)
          createForm.resetFields()
        }}
        okText="创建"
        cancelText="取消"
        okButtonProps={{ loading: createSaving }}
        onOk={submitCreate}
        destroyOnHidden={true}
        width="60%"
      >
        {renderProviderPicker(createProviderValue, (provider) => {
          createForm.setFieldValue('provider', provider)
        })}

        <Form
          form={createForm}
          layout="vertical"
          initialValues={{
            provider: 'openai',
            mode: 'all',
            base_url: 'https://api.openai.com/v1',
            chat_model: 'gpt-4.1-mini',
            embedding_model: 'text-embedding-3-small',
            data_policy: 'chunks_only',
            is_default: false,
          }}
        >
          <div className={styles.formGrid}>
            <Form.Item label="名称" name="name" rules={[{ required: true, message: '请输入名称' }]}>
              <Input placeholder="例如: OpenAI / Azure / 本地 Ollama" />
            </Form.Item>

            <Form.Item label="提供方" name="provider" rules={[{ required: true, message: '请选择提供方' }]}>
              <Select
                showSearch
                options={cloudProviderOptions}
                placeholder="请选择提供方"
                filterOption={selectLabelFilter}
              />
            </Form.Item>

            <Form.Item label="Base URL" name="base_url" rules={[{ required: true, message: '请输入 Base URL' }]}>
              <Input placeholder="例如：https://api.openai.com/v1" />
            </Form.Item>

            <Form.Item label="API Key" name="api_key" rules={[{ required: true, message: '请输入 API Key' }]}>
              <Input.Password placeholder="创建新配置需要填写" autoComplete="new-password" />
            </Form.Item>

            <Form.Item
              label="对话模型"
              name="chat_model"
              rules={[
                {
                  validator: async (_, value) => {
                    if (!createChatModelRequired) return
                    const v = String(value ?? '').trim()
                    if (!v) throw new Error('请输入对话模型')
                  },
                },
              ]}
            >
              <Select
                showSearch
                options={createChatModelOptions}
                placeholder="请选择对话模型"
                filterOption={selectLabelFilter}
              />
            </Form.Item>
          </div>
        </Form>
      </Modal>
    </div>
  )
}
