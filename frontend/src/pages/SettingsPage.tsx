import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { api } from '../api/client'
import type { NotificationStatus, Settings } from '../types'

const PROVIDERS = ['openai', 'anthropic', 'ollama', 'openrouter'] as const

type ModelGroup = { group: string; models: string[] }

const MODELS_BY_PROVIDER: Record<string, ModelGroup[]> = {
  openai: [
    { group: 'GPT-4o', models: ['gpt-4o', 'gpt-4o-mini'] },
    { group: 'o-series', models: ['o1', 'o1-mini', 'o3', 'o3-mini', 'o4-mini'] },
    { group: 'GPT-4', models: ['gpt-4-turbo', 'gpt-4'] },
    { group: 'GPT-3.5', models: ['gpt-3.5-turbo'] },
  ],
  anthropic: [
    { group: 'Claude 4', models: ['claude-opus-4-7', 'claude-sonnet-4-6'] },
    { group: 'Claude 3.7', models: ['claude-3-7-sonnet-20250219'] },
    { group: 'Claude 3.5', models: ['claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022', 'claude-haiku-4-5-20251001'] },
    { group: 'Claude 3', models: ['claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307'] },
  ],
  ollama: [
    { group: 'Llama', models: ['llama3.3', 'llama3.2', 'llama3.1', 'llama3', 'llama2'] },
    { group: 'Mistral', models: ['mistral', 'mistral-nemo', 'mixtral'] },
    { group: 'Qwen', models: ['qwen2.5', 'qwen2.5-coder', 'qwen2.5-coder:7b', 'qwen2.5-coder:32b'] },
    { group: 'DeepSeek', models: ['deepseek-r1', 'deepseek-coder-v2', 'deepseek-v3'] },
    { group: 'Other', models: ['phi4', 'phi3', 'gemma2', 'gemma3', 'codellama', 'starcoder2'] },
  ],
  openrouter: [
    { group: 'OpenAI', models: ['openai/gpt-4o', 'openai/gpt-4o-mini', 'openai/o1', 'openai/o3-mini'] },
    { group: 'Anthropic', models: ['anthropic/claude-sonnet-4-6', 'anthropic/claude-3.5-sonnet', 'anthropic/claude-3.5-haiku', 'anthropic/claude-3-haiku'] },
    { group: 'Meta', models: ['meta-llama/llama-3.3-70b-instruct', 'meta-llama/llama-3.1-70b-instruct', 'meta-llama/llama-3.1-8b-instruct:free'] },
    { group: 'Google', models: ['google/gemini-2.0-flash-001', 'google/gemini-flash-1.5', 'google/gemini-pro-1.5'] },
    { group: 'Mistral', models: ['mistralai/mistral-large-2411', 'mistralai/mistral-small-3.1-24b-instruct:free'] },
    { group: 'DeepSeek', models: ['deepseek/deepseek-r1', 'deepseek/deepseek-chat-v3-0324:free'] },
    { group: 'Qwen', models: ['qwen/qwen-2.5-72b-instruct', 'qwen/qwen-2.5-coder-32b-instruct'] },
  ],
}

// ── Model combobox ────────────────────────────────────────────────────────────

function ModelSelect({
  provider,
  value,
  onChange,
}: {
  provider: string
  value: string
  onChange: (v: string) => void
}) {
  const groups = MODELS_BY_PROVIDER[provider] ?? []
  const allModels = groups.flatMap((g) => g.models)

  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [menuPos, setMenuPos] = useState({ top: 0, left: 0, width: 0 })
  const ref = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  function updateMenuPos() {
    if (!ref.current) return
    const rect = ref.current.getBoundingClientRect()
    setMenuPos({ top: rect.bottom + 6, left: rect.left, width: rect.width })
  }

  useLayoutEffect(() => {
    if (!open) return
    updateMenuPos()
    window.addEventListener('resize', updateMenuPos)
    window.addEventListener('scroll', updateMenuPos, true)
    return () => {
      window.removeEventListener('resize', updateMenuPos)
      window.removeEventListener('scroll', updateMenuPos, true)
    }
  }, [open])

  // Close on outside click
  useEffect(() => {
    if (!open) return
    function handler(e: MouseEvent) {
      const target = e.target as Node
      if (ref.current?.contains(target)) return
      if ((target as Element).closest?.('[data-model-select-menu]')) return
      setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  const q = query.toLowerCase()
  const filtered: ModelGroup[] = query
    ? [{ group: 'Results', models: allModels.filter((m) => m.includes(q)) }]
    : groups

  const isKnown = allModels.includes(value)

  function select(m: string) {
    onChange(m)
    setQuery('')
    setOpen(false)
  }

  const inputStyle = {
    background: 'var(--surface-raised)',
    color: 'var(--text-secondary)',
  }

  return (
    <div ref={ref} className="relative">
      {/* Trigger */}
      <button
        type="button"
        onClick={() => { setOpen((v) => !v); setTimeout(() => inputRef.current?.focus(), 50) }}
        className="w-full flex items-center justify-between px-4 py-2.5 rounded-[12px] text-[13px] text-left transition-colors"
        style={{ ...inputStyle, border: '1px solid var(--glass-border)' }}
      >
        <span style={{ color: value ? 'var(--text-secondary)' : 'var(--text-faint)' }}>
          {value || 'Select a model…'}
          {value && !isKnown && (
            <span className="ml-2 text-[10px] font-semibold px-1.5 py-0.5 rounded" style={{ background: 'color-mix(in srgb, var(--accent-warm) 15%, transparent)', color: 'var(--accent-warm)' }}>
              custom
            </span>
          )}
        </span>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"
          className={`transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
          style={{ color: 'var(--text-faint)' }}>
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {/* Dropdown */}
      {open && createPortal(
        <div
          data-model-select-menu
          className="rounded-[14px] overflow-hidden"
          style={{
            position: 'fixed',
            top: menuPos.top,
            left: menuPos.left,
            width: menuPos.width,
            zIndex: 9999,
            background: 'var(--glass-strong)',
            backdropFilter: 'blur(24px) saturate(200%)',
            WebkitBackdropFilter: 'blur(24px) saturate(200%)',
            border: '1px solid var(--glass-border)',
            boxShadow: '0 16px 48px rgba(15, 23, 42, 0.14)',
          }}
        >
          {/* Search */}
          <div className="p-2" style={{ borderBottom: '1px solid var(--glass-border)' }}>
            <div className="flex items-center gap-2 px-3 py-2 rounded-[10px]" style={{ background: 'var(--surface-raised)' }}>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" style={{ color: 'var(--text-faint)', flexShrink: 0 }}>
                <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              <input
                ref={inputRef}
                type="text"
                placeholder="Search or type custom model…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && query.trim()) select(query.trim())
                  if (e.key === 'Escape') setOpen(false)
                }}
                className="flex-1 bg-transparent text-[13px] focus:outline-none"
                style={{ color: 'var(--text-secondary)' }}
              />
            </div>
          </div>

          {/* List */}
          <div className="max-h-64 overflow-y-auto py-1">
            {filtered.map(({ group, models: ms }) => (
              <div key={group}>
                <div className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-widest" style={{ color: 'var(--text-faint)' }}>
                  {group}
                </div>
                {ms.map((m) => (
                  <button
                    key={m}
                    type="button"
                    onClick={() => select(m)}
                    className="w-full flex items-center justify-between px-4 py-2 text-[13px] text-left transition-colors"
                    style={{
                      color: m === value ? 'var(--accent)' : 'var(--text-secondary)',
                      background: m === value ? 'color-mix(in srgb, var(--accent) 8%, transparent)' : 'transparent',
                    }}
                    onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = 'var(--surface-raised)' }}
                    onMouseLeave={(e) => {
                      (e.currentTarget as HTMLElement).style.background =
                        m === value ? 'color-mix(in srgb, var(--accent) 8%, transparent)' : 'transparent'
                    }}
                  >
                    {m}
                    {m === value && (
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" style={{ color: 'var(--accent)' }}>
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    )}
                  </button>
                ))}
              </div>
            ))}

            {/* Custom entry when query has no match */}
            {query.trim() && !allModels.some((m) => m === query.trim()) && (
              <div>
                <div className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-widest" style={{ color: 'var(--text-faint)' }}>
                  Custom
                </div>
                <button
                  type="button"
                  onClick={() => select(query.trim())}
                  className="w-full flex items-center gap-2 px-4 py-2 text-[13px] text-left"
                  style={{ color: 'var(--accent-warm)' }}
                  onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = 'var(--surface-raised)' }}
                  onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = 'transparent' }}
                >
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                  Use "{query.trim()}"
                </button>
              </div>
            )}

            {filtered[0]?.models.length === 0 && !query.trim() && (
              <div className="px-4 py-6 text-center text-[12px]" style={{ color: 'var(--text-faint)' }}>
                No models for this provider
              </div>
            )}
          </div>
        </div>,
        document.body,
      )}
    </div>
  )
}

// ── Field wrapper ─────────────────────────────────────────────────────────────

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <label className="block text-[13px] font-semibold" style={{ color: 'var(--text-secondary)' }}>{label}</label>
      {children}
      {hint && <p className="text-[11px]" style={{ color: 'var(--text-faint)' }}>{hint}</p>}
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null)
  const [form, setForm] = useState({
    llm_provider: 'openai',
    llm_api_key: '',
    llm_model: 'gpt-4o-mini',
    llm_base_url: '',
    // Notification fields
    notify_enabled: false,
    notify_time: '21:00',
    notify_channels: [] as string[],
    discord_webhook_url: '',
    slack_webhook_url: '',
    slack_bot_token: '',
  })
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [showKey, setShowKey] = useState(false)
  const [loading, setLoading] = useState(true)
  const [notifStatus, setNotifStatus] = useState<NotificationStatus | null>(null)
  const [testingChannel, setTestingChannel] = useState<string | null>(null)
  const [testResult, setTestResult] = useState<Record<string, string>>({})
  const [sendingNow, setSendingNow] = useState(false)

  useEffect(() => {
    Promise.all([api.getSettings(), api.notificationStatus().catch(() => null)]).then(([s, ns]) => {
      setSettings(s)
      setForm({
        llm_provider: s.llm_provider,
        llm_api_key: '',
        llm_model: s.llm_model,
        llm_base_url: s.llm_base_url,
        notify_enabled: s.notify_enabled ?? false,
        notify_time: s.notify_time ?? '21:00',
        notify_channels: (s.notify_channels ?? []).filter((c) => c === 'discord' || c === 'slack'),
        discord_webhook_url: s.discord_webhook_url ?? '',
        slack_webhook_url: s.slack_webhook_url ?? '',
        slack_bot_token: '',
      })
      if (ns) setNotifStatus(ns)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  // When provider changes, auto-select first model in that provider's list
  function setProvider(p: string) {
    const firstModel = MODELS_BY_PROVIDER[p]?.[0]?.models[0] ?? ''
    setForm((f) => ({ ...f, llm_provider: p, llm_model: firstModel }))
  }

  async function save() {
    setSaving(true)
    setSaved(false)
    try {
      const payload: Record<string, unknown> = {
        llm_provider: form.llm_provider,
        llm_model: form.llm_model,
        llm_base_url: form.llm_base_url,
        notify_enabled: form.notify_enabled,
        notify_time: form.notify_time,
        notify_channels: form.notify_channels.filter((c) => c === 'discord' || c === 'slack'),
        discord_webhook_url: form.discord_webhook_url,
        slack_webhook_url: form.slack_webhook_url,
      }
      if (form.llm_api_key.trim()) payload.llm_api_key = form.llm_api_key.trim()
      if (form.slack_bot_token.trim()) payload.slack_bot_token = form.slack_bot_token.trim()
      await api.saveSettings(payload as Parameters<typeof api.saveSettings>[0])
      await api.reloadSchedule().catch(() => {})
      const [fresh, ns] = await Promise.all([api.getSettings(), api.notificationStatus().catch(() => null)])
      setSettings(fresh)
      if (ns) setNotifStatus(ns)
      setForm((f) => ({ ...f, llm_api_key: '', slack_bot_token: '' }))
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch { /* ignore */ }
    setSaving(false)
  }

  function toggleChannel(ch: string) {
    setForm((f) => ({
      ...f,
      notify_channels: f.notify_channels.includes(ch)
        ? f.notify_channels.filter((c) => c !== ch)
        : [...f.notify_channels, ch],
    }))
  }

  async function saveNotificationSettings() {
    await api.saveSettings({
      notify_enabled: form.notify_enabled,
      notify_time: form.notify_time,
      notify_channels: form.notify_channels.filter((c) => c === 'discord' || c === 'slack'),
      discord_webhook_url: form.discord_webhook_url.trim(),
      slack_webhook_url: form.slack_webhook_url.trim(),
    })
  }

  async function testChannel(platform: string) {
    setTestingChannel(platform)
    setTestResult((r) => ({ ...r, [platform]: '' }))
    try {
      if (platform === 'discord' && !form.discord_webhook_url.trim()) {
        setTestResult((r) => ({
          ...r,
          [platform]: 'error: paste your Discord webhook URL above first',
        }))
        return
      }
      // Test reads ~/.deepreflect/config.json — save form values first
      await saveNotificationSettings()
      const res = await api.testNotification(platform)
      setTestResult((r) => ({ ...r, [platform]: res.result }))
    } catch (e: unknown) {
      setTestResult((r) => ({ ...r, [platform]: String(e) }))
    }
    setTestingChannel(null)
  }

  async function sendNow() {
    setSendingNow(true)
    try {
      await saveNotificationSettings()
      const res = await api.sendNotificationNow()
      const summary = Object.entries(res.results).map(([k, v]) => `${k}: ${v}`).join(' · ')
      setTestResult((r) => ({ ...r, _all: summary }))
    } catch (e: unknown) {
      setTestResult((r) => ({ ...r, _all: String(e) }))
    }
    setSendingNow(false)
  }

  const inputCls = 'w-full px-4 py-2.5 rounded-[12px] text-[13px] transition-colors focus:outline-none'
  const inputStyle = { background: 'var(--surface-raised)', border: '1px solid var(--glass-border)', color: 'var(--text-secondary)' }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-8 h-8 border-2 rounded-full animate-spin"
          style={{ borderColor: 'color-mix(in srgb, var(--accent) 30%, transparent)', borderTopColor: 'var(--accent)' }} />
      </div>
    )
  }

  return (
    <div className="p-8 lg:p-10 max-w-2xl mx-auto space-y-6">
      <div className="animate-fade-in-up">
        <h1 className="font-display text-3xl font-extrabold tracking-tight" style={{ color: 'var(--text-primary)' }}>Settings</h1>
        <p className="text-sm mt-1.5" style={{ color: 'var(--text-muted)' }}>Configure your LLM provider and preferences.</p>
      </div>

      {/* LLM PROVIDER */}
      <div className="glass p-6 space-y-5 animate-fade-in-up stagger-1">
        <div className="section-label">LLM Provider</div>

        <Field label="Provider">
          <div className="flex gap-2 flex-wrap">
            {PROVIDERS.map((p) => (
              <button key={p} type="button" onClick={() => setProvider(p)}
                className="px-4 py-2 text-[12px] font-semibold rounded-[10px] transition-all cursor-pointer"
                style={{
                  background: form.llm_provider === p
                    ? 'color-mix(in srgb, var(--accent) 15%, transparent)'
                    : 'var(--surface-raised)',
                  color: form.llm_provider === p ? 'var(--accent)' : 'var(--text-muted)',
                  border: form.llm_provider === p
                    ? '1px solid color-mix(in srgb, var(--accent) 30%, transparent)'
                    : '1px solid var(--glass-border)',
                }}>
                {p}
              </button>
            ))}
          </div>
        </Field>

        <Field label="API Key"
          hint={settings?.llm_api_key_set
            ? `Current key: ${settings.llm_api_key_masked} — leave blank to keep`
            : 'Required for cloud providers. Not needed for Ollama.'}>
          <div className="relative">
            <input
              type={showKey ? 'text' : 'password'}
              placeholder={settings?.llm_api_key_set ? '(unchanged)' : 'sk-…'}
              value={form.llm_api_key}
              onChange={(e) => setForm((f) => ({ ...f, llm_api_key: e.target.value }))}
              className={inputCls}
              style={{ ...inputStyle, paddingRight: 44 }}
            />
            <button type="button" onClick={() => setShowKey((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 cursor-pointer"
              style={{ color: 'var(--text-faint)' }}>
              {showKey
                ? <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                : <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
              }
            </button>
          </div>
        </Field>

        <Field label="Model" hint="Pick from the list or type a custom model name and press Enter.">
          <ModelSelect
            provider={form.llm_provider}
            value={form.llm_model}
            onChange={(m) => setForm((f) => ({ ...f, llm_model: m }))}
          />
        </Field>

        <Field label="Custom Base URL"
          hint={form.llm_provider === 'ollama'
            ? 'Default: http://localhost:11434/v1'
            : 'Override the default API endpoint (leave blank to use provider default).'}>
          <input
            type="text"
            placeholder={form.llm_provider === 'ollama' ? 'http://localhost:11434/v1' : 'https://…'}
            value={form.llm_base_url}
            onChange={(e) => setForm((f) => ({ ...f, llm_base_url: e.target.value }))}
            className={inputCls}
            style={inputStyle}
          />
        </Field>
      </div>

      {/* NOTIFICATIONS */}
      <div className="glass p-6 space-y-5 animate-fade-in-up stagger-2">
        <div className="flex items-center justify-between">
          <div className="section-label">Daily Notifications</div>
          {/* Enable toggle */}
          <button
            type="button"
            onClick={() => setForm((f) => ({ ...f, notify_enabled: !f.notify_enabled }))}
            className="flex items-center gap-2 px-3 py-1.5 rounded-full text-[12px] font-semibold transition-all cursor-pointer"
            style={{
              background: form.notify_enabled
                ? 'color-mix(in srgb, var(--accent-green) 15%, transparent)'
                : 'var(--surface-raised)',
              color: form.notify_enabled ? 'var(--accent-green)' : 'var(--text-muted)',
              border: form.notify_enabled
                ? '1px solid color-mix(in srgb, var(--accent-green) 30%, transparent)'
                : '1px solid var(--glass-border)',
            }}
          >
            <div className="w-2 h-2 rounded-full" style={{ background: form.notify_enabled ? 'var(--accent-green)' : 'var(--text-faint)' }} />
            {form.notify_enabled ? 'Enabled' : 'Disabled'}
          </button>
        </div>

        <Field label="Send daily roast at" hint="Local time — fires while 'deepreflect serve' is running.">
          <input
            type="time"
            value={form.notify_time}
            onChange={(e) => setForm((f) => ({ ...f, notify_time: e.target.value }))}
            className={inputCls}
            style={inputStyle}
          />
        </Field>

        {/* Status row */}
        {notifStatus && (
          <div className="flex items-center gap-4 text-[11px]" style={{ color: 'var(--text-faint)' }}>
            {notifStatus.last_sent && (
              <span>Last sent: {new Date(notifStatus.last_sent).toLocaleString()}</span>
            )}
            {notifStatus.next_fire_time && (
              <span>Next: {new Date(notifStatus.next_fire_time).toLocaleString()}</span>
            )}
          </div>
        )}

        {/* Channel cards */}
        {[
          {
            key: 'discord',
            label: 'Discord',
            icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="var(--accent)" style={{ flexShrink: 0 }}><path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057c.002.022.015.04.037.05a19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03z"/></svg>,
            color: '--accent',
            fields: [{
              key: 'discord_webhook_url' as const,
              label: 'Webhook URL',
              placeholder: 'https://discord.com/api/webhooks/…',
              hint: 'Full URL from Discord channel → Integrations → Webhooks. Test auto-saves this field.',
            }],
          },
          {
            key: 'slack',
            label: 'Slack',
            icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="var(--accent-green)" style={{ flexShrink: 0 }}><path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312zM18.956 8.834a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 0 1-2.523 2.521 2.527 2.527 0 0 1-2.52-2.521V2.522A2.527 2.527 0 0 1 15.165 0a2.528 2.528 0 0 1 2.523 2.522v6.312zM15.165 18.956a2.528 2.528 0 0 1 2.523 2.522A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.52-2.522v-2.522h2.52zM15.165 17.688a2.527 2.527 0 0 1-2.52-2.523 2.526 2.526 0 0 1 2.52-2.52h6.313A2.527 2.527 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.523h-6.313z"/></svg>,
            color: '--accent-green',
            fields: [
              { key: 'slack_webhook_url' as const, label: 'Incoming Webhook URL', placeholder: 'https://hooks.slack.com/services/…' },
              { key: 'slack_bot_token' as const, label: 'Bot Token (optional, for image)', placeholder: 'xoxb-… (needs files:write scope)' },
            ],
          },
        ].map((ch) => {
          const active = form.notify_channels.includes(ch.key)
          const result = testResult[ch.key]
          return (
            <div key={ch.key} className="glass-subtle rounded-[16px] p-4 space-y-3"
              style={{ border: active ? `1px solid color-mix(in srgb, var(${ch.color}) 25%, transparent)` : undefined }}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {ch.icon}
                  <span className="text-[13px] font-semibold" style={{ color: 'var(--text-secondary)' }}>{ch.label}</span>
                </div>
                <div className="flex items-center gap-2">
                  {active && (
                    <button
                      type="button"
                      onClick={() => testChannel(ch.key)}
                      disabled={testingChannel === ch.key}
                      className="px-3 py-1 text-[11px] font-semibold rounded-full transition-all disabled:opacity-40 cursor-pointer"
                      style={{ background: `color-mix(in srgb, var(${ch.color}) 12%, transparent)`, color: `var(${ch.color})`, border: `1px solid color-mix(in srgb, var(${ch.color}) 20%, transparent)` }}
                    >
                      {testingChannel === ch.key ? 'Sending…' : 'Test'}
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => toggleChannel(ch.key)}
                    className="px-3 py-1.5 text-[11px] font-semibold rounded-full transition-all cursor-pointer"
                    style={{
                      background: active ? `color-mix(in srgb, var(${ch.color}) 15%, transparent)` : 'var(--surface-raised)',
                      color: active ? `var(${ch.color})` : 'var(--text-muted)',
                      border: active ? `1px solid color-mix(in srgb, var(${ch.color}) 30%, transparent)` : '1px solid var(--glass-border)',
                    }}
                  >
                    {active ? 'On' : 'Off'}
                  </button>
                </div>
              </div>

              {'warning' in ch && typeof ch.warning === 'string' ? (
                <p className="text-[11px]" style={{ color: 'var(--accent-warm)' }}>{ch.warning}</p>
              ) : null}

              {active && ch.fields.map((f) => (
                <div key={f.key}>
                  <label className="block text-[11px] font-medium mb-1" style={{ color: 'var(--text-muted)' }}>{f.label}</label>
                  {'hint' in f && f.hint ? (
                    <p className="text-[10px] mb-1.5" style={{ color: 'var(--text-faint)' }}>{f.hint}</p>
                  ) : null}
                  <input
                    type={f.key === 'slack_bot_token' ? 'password' : 'text'}
                    placeholder={f.placeholder}
                    value={form[f.key]}
                    onChange={(e) => setForm((prev) => ({ ...prev, [f.key]: e.target.value }))}
                    className={inputCls}
                    style={inputStyle}
                  />
                </div>
              ))}

              {result && (
                <p className="text-[11px] px-1" style={{ color: result === 'ok' ? 'var(--accent-green)' : 'var(--accent-pink)' }}>
                  {result === 'ok' ? '✓ Sent successfully' : result}
                </p>
              )}
            </div>
          )
        })}

        {/* Send now */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={sendNow}
            disabled={sendingNow || form.notify_channels.length === 0}
            className="glass-subtle px-4 py-2.5 text-[13px] font-medium transition-all disabled:opacity-40 flex items-center gap-2 cursor-pointer"
            style={{ color: 'var(--text-secondary)' }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
            {sendingNow ? 'Sending…' : 'Send Now'}
          </button>
          {testResult._all && (
            <span className="text-[11px]" style={{ color: 'var(--text-muted)' }}>{testResult._all}</span>
          )}
        </div>
      </div>

      {/* SAVE */}
      <div className="flex items-center gap-4 animate-fade-in-up stagger-3">
        <button type="button" onClick={save} disabled={saving}
          className="flex-1 py-3 text-[13px] font-semibold rounded-[14px] transition-all disabled:opacity-40 flex items-center justify-center gap-2 cursor-pointer"
          style={{
            background: 'linear-gradient(135deg, var(--accent), var(--accent-secondary))',
            color: 'white',
            boxShadow: '0 4px 20px color-mix(in srgb, var(--accent) 25%, transparent)',
          }}>
          {saving
            ? <><div className="w-4 h-4 border-2 rounded-full animate-spin"
                style={{ borderColor: 'rgba(255,255,255,.3)', borderTopColor: 'white' }} />Saving…</>
            : <><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>Save Settings</>
          }
        </button>
        {saved && (
          <div className="flex items-center gap-1.5 text-[13px] font-medium animate-fade-in"
            style={{ color: 'var(--accent-green)' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>
            Saved!
          </div>
        )}
      </div>

      {/* INFO */}
      {settings && (
        <div className="glass-subtle p-5 rounded-[16px] space-y-2 animate-fade-in-up stagger-4">
          <div className="section-label mb-3">System Info</div>
          {[['Data directory', settings.data_dir], ['Server port', String(settings.port)]].map(([k, v]) => (
            <div key={k} className="flex items-start justify-between gap-4 text-[12px]">
              <span style={{ color: 'var(--text-faint)' }}>{k}</span>
              <span className="font-mono text-right" style={{ color: 'var(--text-muted)', wordBreak: 'break-all' }}>{v}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
