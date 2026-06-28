# Mnemivo for Home Assistant

A [Home Assistant](https://www.home-assistant.io/) custom integration that exposes Mnemivo shopping lists as native **todo entities** — with two-way sync, voice assistant support, and automations.

## Features

- Native `todo.*` entities — one per selected shopping list
- Check off items in HA → syncs to the Mnemivo app
- Add items via voice ("Hey Google, add Milk to Mnemivo")
- Automations: notify when the list changes, reset checked items at midnight, etc.
- Polls every 30 seconds; optimistic updates feel instant

## Prerequisites

- A Mnemivo account (signed in on the app)
- Home Assistant 2024.6 or newer

---

## Setup

### Step 1 — Get your personal API token

Open the **Mnemivo app → Settings → Home Assistant Token** and tap **Generate token**.

Copy both values shown:
- **Edge Function URL** — the same for all users
- **Token** — personal to your account, shown only once

> You must be signed in to generate a token.

### Step 2 — Install the integration

**Option A: HACS (recommended)**

1. In HACS, go to **Integrations → Custom repositories**
2. Add `https://github.com/DSchreyer/mnemivo-homeassistant` as an **Integration**
3. Search for "Mnemivo" and install

**Option B: Manual**

Copy the `custom_components/mnemivo/` folder into your HA config directory:

```bash
cp -r custom_components/mnemivo  /path/to/homeassistant/config/custom_components/
```

Restart Home Assistant.

### Step 3 — Configure in HA

1. Go to **Settings → Integrations → Add Integration**
2. Search for **Mnemivo**
3. Enter:
   - **Edge Function URL** — `https://<your-project-ref>.supabase.co/functions/v1/ha-api`
   - **API Token** — the token you generated in Step 1
4. Select which shopping lists to expose

---

## Usage

Each selected list becomes a `todo.*` entity (e.g. `todo.einkaufsliste`).

### Dashboard card

```yaml
type: todo-list
entity: todo.einkaufsliste
```

### Add an item via service call

```yaml
service: todo.add_item
target:
  entity_id: todo.einkaufsliste
data:
  item: Milch
```

### Automation example — remind when leaving home

```yaml
automation:
  trigger:
    platform: zone
    entity_id: person.daniel
    zone: zone.home
    event: leave
  condition:
    condition: template
    value_template: "{{ state_attr('todo.einkaufsliste', 'items') | selectattr('status', 'eq', 'needs_action') | list | count > 0 }}"
  action:
    service: notify.mobile_app
    data:
      message: "Du hast {{ state_attr('todo.einkaufsliste', 'items') | selectattr('status', 'eq', 'needs_action') | list | count }} Artikel auf der Einkaufsliste."
```

---

## How sync works

| Direction | Trigger | Latency |
|-----------|---------|---------|
| App → HA | HA polls every 30 s | ≤ 30 s |
| HA → App | Immediate write to Supabase; app pulls on next sync | ≤ 2 min |

Items created in HA appear in the app as soon as the app's sync engine runs (usually within 2 seconds if the app is open, up to 2 minutes in the background).

---

## Troubleshooting

**"Cannot connect"** — Check the Edge Function URL and make sure the function is deployed.

**"Invalid auth"** — Regenerate your token in the Mnemivo app (Settings → Home Assistant Token → Regenerate token) and update it in HA.

**Items not appearing in the app** — Make sure the list's space is set to cloud sync in the Mnemivo app settings.
