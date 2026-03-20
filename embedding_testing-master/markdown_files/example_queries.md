# Example Queries and Component Mapping

This is the most important file for RAG retrieval.
It maps natural language user queries to the relevant component snippets that should be retrieved.

---

## Dashboard Queries

**"make me a dashboard"**
→ `snippet_10_dashboard_layout`, `snippet_09_card`, `snippet_06_sidebar`

**"I need an admin panel with stats"**
→ `snippet_10_dashboard_layout`, `snippet_09_card`

**"build an analytics overview page"**
→ `snippet_10_dashboard_layout`, `snippet_09_card`, `snippet_06_sidebar`

**"create a home page with metric cards showing users and revenue"**
→ `snippet_09_card`, `snippet_10_dashboard_layout`

**"I want a page with KPI cards at the top"**
→ `snippet_09_card`, `snippet_10_dashboard_layout`

---

## Table and Data Queries

**"show me a list of users in a table"**
→ `snippet_03_data_table`, `snippet_02_search_bar`

**"I need a data grid with search"**
→ `snippet_03_data_table`, `snippet_02_search_bar`

**"build a table with search and pagination"**
→ `snippet_03_data_table`, `snippet_02_search_bar`, `snippet_08_pagination`

**"display records with filtering and page navigation"**
→ `snippet_03_data_table`, `snippet_02_search_bar`, `snippet_08_pagination`

**"I need to show a list of products with next/prev page buttons"**
→ `snippet_03_data_table`, `snippet_08_pagination`

---

## Form and Modal Queries

**"add a popup form to create a new user"**
→ `snippet_04_modal`, `snippet_05_form`, `snippet_01_button`

**"I need a modal with a form inside"**
→ `snippet_04_modal`, `snippet_05_form`

**"show a dialog box when the user clicks add"**
→ `snippet_04_modal`, `snippet_01_button`

**"create a form with validation for name and email"**
→ `snippet_05_form`

**"I need an edit form that opens as an overlay"**
→ `snippet_04_modal`, `snippet_05_form`, `snippet_01_button`

---

## Notification Queries

**"show a success message after form submit"**
→ `snippet_07_toast`, `snippet_05_form`

**"I need toast notifications for errors and success"**
→ `snippet_07_toast`

**"display an alert when an action completes"**
→ `snippet_07_toast`

**"show a green notification when saved and red when failed"**
→ `snippet_07_toast`

---

## Navigation and Layout Queries

**"I need a sidebar with navigation links"**
→ `snippet_06_sidebar`

**"build a collapsible left menu"**
→ `snippet_06_sidebar`

**"create an app layout with a left nav panel"**
→ `snippet_06_sidebar`, `snippet_10_dashboard_layout`

**"I want a side navigation that collapses to icons"**
→ `snippet_06_sidebar`

---

## Button and Action Queries

**"add a delete button in red"**
→ `snippet_01_button` (variant: danger)

**"I need a primary and secondary action button"**
→ `snippet_01_button`

**"create a disabled submit button"**
→ `snippet_01_button` (disabled: true)

---

## Search Queries

**"add a search input that filters as I type"**
→ `snippet_02_search_bar`

**"I need a debounced search box"**
→ `snippet_02_search_bar`

**"live search input for filtering a list"**
→ `snippet_02_search_bar`, `snippet_03_data_table`

---

## Pagination Queries

**"add page navigation below the table"**
→ `snippet_08_pagination`, `snippet_03_data_table`

**"I need next/prev buttons with page numbers"**
→ `snippet_08_pagination`

**"paginate my list of 100 items, 10 per page"**
→ `snippet_08_pagination`

---

## Combined / Complex Queries

**"full dashboard with sidebar, stats, table, search, and pagination"**
→ `snippet_10_dashboard_layout`, `snippet_06_sidebar`, `snippet_09_card`, `snippet_02_search_bar`, `snippet_03_data_table`, `snippet_08_pagination`

**"admin panel where I can view users, search them, and add a new one via a form"**
→ `snippet_10_dashboard_layout`, `snippet_03_data_table`, `snippet_02_search_bar`, `snippet_04_modal`, `snippet_05_form`, `snippet_01_button`

**"dashboard with cards and a table below, show toast on row delete"**
→ `snippet_09_card`, `snippet_03_data_table`, `snippet_07_toast`, `snippet_01_button`
