# Mnemivo for Home Assistant

A [Home Assistant](https://www.home-assistant.io/) custom integration that exposes your Mnemivo shopping lists as native **todo entities** — with two-way live sync, voice assistant support, and automations.

## What you get

- Native `todo.*` entities in HA — one per selected list
- Check off items in HA → syncs to the Mnemivo app (and vice versa)
- Add items via voice: *"Hey Google, add Milk to my shopping list"*
- Use in automations: notify when you leave home, reset the list after shopping, etc.
- Polls every 30 seconds; writes feel instant (optimistic updates)

---

## Installation

### Step 1 — Install the integration in Home Assistant

**Option A: HACS (recommended)**

1. Open HACS → Integrations
2. Click the three-dot menu → **Custom repositories**
3. Add `https://github.com/DSchreyer/mnemivo-homeassistant` as type **Integration**
4. Search for **Mnemivo** and install
5. Restart Home Assistant

**Option B: Manual**

Download or clone this repo, then copy the `custom_components/mnemivo/` folder into your HA config directory:

```
<HA config>/
└── custom_components/
    └── mnemivo/       ← copy this folder here
```

Restart Home Assistant.

---

### Step 2 — Generate your personal API token

Every Mnemivo user gets their own token — no shared secrets, no developer tools needed.

1. Open the **Mnemivo app**
2. Go to **Settings → Home Assistant Token**
3. Tap **Generate token**
4. You will see two values — **copy both**:
   - **Edge Function URL** (same for all users)
   - **Your token** (personal to your account — shown only once)

> You must be signed in to the Mnemivo app to generate a token.

---

### Step 3 — Connect in Home Assistant

1. Go to **Settings → Integrations → Add Integration**
2. Search for **Mnemivo**
3. Enter the **Edge Function URL** and your **token** from Step 2
4. Select which lists to expose in Home Assistant
5. Done ✓

---

## Usage

Each selected list becomes a `todo.*` entity (e.g. `todo.einkaufsliste`).

### Shopping list dashboard card

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

### Automation — remind when leaving home

```yaml
automation:
  trigger:
    platform: zone
    entity_id: person.daniel
    zone: zone.home
    event: leave
  condition:
    condition: template
    value_template: >
      {{ state_attr('todo.einkaufsliste', 'items')
         | selectattr('status', 'eq', 'needs_action')
         | list | count > 0 }}
  action:
    service: notify.mobile_app
    data:
      message: >
        {{ state_attr('todo.einkaufsliste', 'items')
           | selectattr('status', 'eq', 'needs_action')
           | list | count }} items on your shopping list.
```

---

## How sync works

| Direction | How | Latency |
|-----------|-----|---------|
| App → HA | HA polls every 30 s | ≤ 30 s |
| HA → App | Immediate write; app pulls on next sync | ≤ 2 min |

Items added in HA appear in the app as soon as the app syncs (typically within a few seconds when the app is open).

---

## Troubleshooting

**"Cannot connect"** — Check the Edge Function URL is correct and your network allows outbound HTTPS.

**"Invalid auth"** — Your token may have been regenerated. Open Mnemivo → Settings → Home Assistant Token → Regenerate, then update the token in HA (delete and re-add the integration).

**Items not syncing to app** — Make sure the list's space is set to cloud sync in the Mnemivo app. Local-only lists are not accessible via the API.

**List not appearing in HA** — Only lists you own or have been invited to are shown. Check you are signed in to the correct account.
