const SELECTED_MODEL_CONFIG_KEY = 'settings.selected_model_config_id'

export function getStoredSelectedModelConfigId(): string | null {
  try {
    const raw = localStorage.getItem(SELECTED_MODEL_CONFIG_KEY)
    return raw && raw.trim() ? raw : null
  } catch {
    return null
  }
}

export function setStoredSelectedModelConfigId(id: string | null) {
  try {
    if (!id) {
      localStorage.removeItem(SELECTED_MODEL_CONFIG_KEY)
      return
    }
    localStorage.setItem(SELECTED_MODEL_CONFIG_KEY, id)
  } catch {}
}
