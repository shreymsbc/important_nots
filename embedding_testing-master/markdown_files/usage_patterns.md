# Component Usage Patterns

This document describes how to combine the 10 components together to build common UI layouts.
Use this as a guide for which snippets to retrieve and compose for a given user request.

---

## Pattern 1: Full Dashboard Page
**Use when:** user wants a dashboard, admin panel, analytics page, overview page

**Components:**
- `snippet_10_dashboard_layout.jsx` → outer shell with sidebar and card grid
- `snippet_09_card.jsx` → stat cards (users, revenue, sessions)
- `snippet_06_sidebar.jsx` → left navigation (already inside layout)

**Structure:**
```
DashboardLayout
  ├── Sidebar (left)
  └── Main
       ├── Card (x3 in grid)
       └── {children} → your page content goes here
```

---

## Pattern 2: Data Table Page with Search and Pagination
**Use when:** user wants to display a list, records, users table, data grid with filtering and paging

**Components:**
- `snippet_02_search_bar.jsx` → filters the table as user types
- `snippet_03_data_table.jsx` → renders the filtered data rows
- `snippet_08_pagination.jsx` → splits records across pages

**Structure:**
```
<SearchBar onSearch={handleSearch} />
<DataTable columns={cols} data={filteredData} />
<Pagination total={total} perPage={10} current={page} onChange={setPage} />
```

---

## Pattern 3: Form Inside a Modal
**Use when:** user wants a popup form, add record dialog, edit user modal, create item overlay

**Components:**
- `snippet_04_modal.jsx` → the overlay dialog wrapper
- `snippet_05_form.jsx` → the form with validation inside the modal
- `snippet_01_button.jsx` → trigger button to open the modal

**Structure:**
```
<Button label="Add User" onClick={() => setOpen(true)} />
<Modal isOpen={open} onClose={() => setOpen(false)} title="Add User">
  <Form onSubmit={handleSubmit} />
</Modal>
```

---

## Pattern 4: Dashboard with Table and Search
**Use when:** user wants a full admin dashboard with a data table below the stat cards

**Components:**
- `snippet_10_dashboard_layout.jsx` → page shell
- `snippet_09_card.jsx` → top metric cards
- `snippet_02_search_bar.jsx` → search above table
- `snippet_03_data_table.jsx` → main data display
- `snippet_08_pagination.jsx` → pagination below table

**Structure:**
```
DashboardLayout
  └── Main
       ├── Card (x3)
       ├── SearchBar
       ├── DataTable
       └── Pagination
```

---

## Pattern 5: Action with Feedback Notification
**Use when:** user wants to show success/error messages, alerts, notifications after an action

**Components:**
- `snippet_07_toast.jsx` → notification system
- `snippet_01_button.jsx` → triggers the action
- `snippet_05_form.jsx` → form that shows toast on submit

**Structure:**
```
const { addToast, ToastContainer } = useToast();

<Form onSubmit={() => addToast("Saved successfully", "success")} />
<ToastContainer />
```

---

## Pattern 6: Sidebar Navigation Layout with Content
**Use when:** user wants a multi-page app shell, nav layout, left menu with content area

**Components:**
- `snippet_06_sidebar.jsx` → collapsible left nav
- Any content component as the right panel

**Structure:**
```
<div className="flex">
  <Sidebar items={navItems} />
  <main className="flex-1 p-6">
    {pageContent}
  </main>
</div>
```
