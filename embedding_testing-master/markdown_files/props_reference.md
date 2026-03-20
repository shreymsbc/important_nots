# Props Reference

Complete props API for all 10 components.

---

## Button (`snippet_01_button.jsx`)

| Prop | Type | Default | Required | Description |
|---|---|---|---|---|
| `label` | string | — | ✅ | Text displayed on the button |
| `onClick` | function | — | ✅ | Click handler function |
| `variant` | `"primary"` \| `"secondary"` \| `"danger"` | `"primary"` | ❌ | Visual style of the button |
| `disabled` | boolean | `false` | ❌ | Disables the button and reduces opacity |

---

## SearchBar (`snippet_02_search_bar.jsx`)

| Prop | Type | Default | Required | Description |
|---|---|---|---|---|
| `onSearch` | function | — | ✅ | Called with the query string after 400ms debounce |
| `placeholder` | string | `"Search..."` | ❌ | Placeholder text inside the input |

---

## DataTable (`snippet_03_data_table.jsx`)

| Prop | Type | Default | Required | Description |
|---|---|---|---|---|
| `columns` | `Array<{ key: string, label: string }>` | — | ✅ | Column definitions. `key` maps to row object field, `label` is the header text |
| `data` | `Array<object>` | — | ✅ | Array of row objects. Each object should have keys matching column `key` values |

---

## Modal (`snippet_04_modal.jsx`)

| Prop | Type | Default | Required | Description |
|---|---|---|---|---|
| `isOpen` | boolean | — | ✅ | Controls modal visibility |
| `onClose` | function | — | ✅ | Called when user clicks ✕ or presses Escape |
| `title` | string | — | ✅ | Title text shown in the modal header |
| `children` | ReactNode | — | ✅ | Content rendered inside the modal body |

---

## Form (`snippet_05_form.jsx`)

| Prop | Type | Default | Required | Description |
|---|---|---|---|---|
| `onSubmit` | function | — | ✅ | Called with `{ name, email }` object when validation passes |

**Internal fields:** `name` (text), `email` (text)
**Validation rules:** name must be non-empty, email must contain `@`

---

## Sidebar (`snippet_06_sidebar.jsx`)

| Prop | Type | Default | Required | Description |
|---|---|---|---|---|
| `items` | `Array<{ label: string, icon: string }>` | — | ✅ | Navigation items. `icon` is typically an emoji or icon character |

**Internal state:** `collapsed` (boolean), `active` (string — currently selected label)

---

## Toast / useToast (`snippet_07_toast.jsx`)

This is a custom hook, not a component. Usage:

```jsx
const { addToast, ToastContainer } = useToast();
```

| Return | Type | Description |
|---|---|---|
| `addToast` | `(message: string, type?: string) => void` | Triggers a toast. Type can be `"info"`, `"success"`, or `"error"` |
| `ToastContainer` | ReactComponent | Mount this once in your app. Renders all active toasts |

**Auto-dismiss:** 3000ms

---

## Pagination (`snippet_08_pagination.jsx`)

| Prop | Type | Default | Required | Description |
|---|---|---|---|---|
| `total` | number | — | ✅ | Total number of records across all pages |
| `perPage` | number | — | ✅ | Number of records per page |
| `current` | number | — | ✅ | Currently active page number (1-indexed) |
| `onChange` | function | — | ✅ | Called with new page number when user clicks a page button |

**Derived:** `pages = Math.ceil(total / perPage)`

---

## Card (`snippet_09_card.jsx`)

| Prop | Type | Default | Required | Description |
|---|---|---|---|---|
| `title` | string | — | ✅ | Small label above the value (e.g. "Total Users") |
| `value` | string \| number | — | ✅ | Large displayed metric (e.g. "1,240" or "$8,430") |
| `icon` | string | — | ✅ | Emoji or icon shown on the right side |
| `trend` | number | — | ❌ | Percentage change vs last month. Positive = green ▲, Negative = red ▼ |

---

## DashboardLayout (`snippet_10_dashboard_layout.jsx`)

| Prop | Type | Default | Required | Description |
|---|---|---|---|---|
| `children` | ReactNode | — | ✅ | Content rendered in the main area below the stat cards |

**Hardcoded internals:**
- Sidebar nav items: Dashboard, Users, Reports, Settings
- 3 stat Cards: Total Users (1,240 ▲12%), Revenue ($8,430 ▼3%), Active Sessions (342 ▲5%)

**To customize:** replace hardcoded `navItems` and Card values with props as needed
