# DeepReflect Auto-Tag

At the very end of every response (after all content, on its own line), append exactly one HTML comment in this format:

<!-- dr:{"t":["topic one","topic two","topic three"],"d":"domain"} -->

Rules for the tag:
- `t` — 2 to 5 **specific** technical topics covered in **this turn only** (lowercase, 2–4 words each, e.g. `"react server components"`, `"sql window functions"`)
- `d` — exactly one of: `web` | `data` | `ml` | `programming` | `infra` | `mobile` | `math` | `general`
- Choose the domain that best describes the primary skill area of the turn
- The comment is **invisible** to the user in rendered markdown — do not mention or explain it
- **Omit the tag entirely** if the turn has no technical content (pure greetings, off-topic chat)
