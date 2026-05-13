import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import type { Settings } from '../types'

const PROVIDERS = ['openai', 'anthropic', 'ollama', 'openrouter'] as const
const TONES = ['friendly', 'strict', 'funny'] as const

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
  const ref = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Close on outside click
  useEffect(() => {
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

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
      {open && (
        <div
          className="absolute left-0 right-0 mt-1.5 rounded-[14px] overflow-hidden z-50"
          style={{
            background: 'var(--glass-strong)',
            backdropFilter: 'blur(24px) saturate(200%)',
            WebkitBackdropFilter: 'blur(24px) saturate(200%)',
            border: '1px solid var(--glass-border)',
            boxShadow: '0 16px 48px rgba(0,0,0,0.35)',
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
        </div>
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
    intervention_tone: 'friendly',
    repeat_threshold: 3,
  })
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [showKey, setShowKey] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getSettings().then((s) => {
      setSettings(s)
      setForm({
        llm_provider: s.llm_provider,
        llm_api_key: '',
        llm_model: s.llm_model,
        llm_base_url: s.llm_base_url,
        intervention_tone: s.intervention_tone,
        repeat_threshold: s.repeat_threshold,
      })
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
        intervention_tone: form.intervention_tone,
        repeat_threshold: form.repeat_threshold,
      }
      if (form.llm_api_key.trim()) payload.llm_api_key = form.llm_api_key.trim()
      await api.saveSettings(payload as Parameters<typeof api.saveSettings>[0])
      const fresh = await api.getSettings()
      setSettings(fresh)
      setForm((f) => ({ ...f, llm_api_key: '' }))
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch { /* ignore */ }
    setSaving(false)
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

      {/* COACH */}
      <div className="glass p-6 space-y-5 animate-fade-in-up stagger-2">
        <div className="section-label">Coach Behavior</div>

        <Field label="Intervention Tone"
          hint="How the coach addresses you when it detects repeated questions.">
          <div className="flex gap-2">
            {TONES.map((t) => (
              <button key={t} type="button" onClick={() => setForm((f) => ({ ...f, intervention_tone: t }))}
                className="flex-1 py-2 text-[12px] font-semibold rounded-[10px] transition-all cursor-pointer capitalize"
                style={{
                  background: form.intervention_tone === t
                    ? 'color-mix(in srgb, var(--accent-warm) 15%, transparent)'
                    : 'var(--surface-raised)',
                  color: form.intervention_tone === t ? 'var(--accent-warm)' : 'var(--text-muted)',
                  border: form.intervention_tone === t
                    ? '1px solid color-mix(in srgb, var(--accent-warm) 30%, transparent)'
                    : '1px solid var(--glass-border)',
                }}>
                {t === 'friendly' ? '😊 Friendly' : t === 'strict' ? '🎯 Strict' : '😂 Funny'}
              </button>
            ))}
          </div>
        </Field>

        <Field label="Repeat Threshold"
          hint="Trigger an intervention after asking about the same concept this many times.">
          <div className="flex items-center gap-4">
            <input type="range" min={1} max={10} value={form.repeat_threshold}
              onChange={(e) => setForm((f) => ({ ...f, repeat_threshold: Number(e.target.value) }))}
              className="flex-1" />
            <span className="font-display text-xl font-bold w-8 text-center"
              style={{ color: 'var(--accent)' }}>
              {form.repeat_threshold}
            </span>
          </div>
        </Field>
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
