# React Components Overview

This document describes all 10 available React components in the knowledge base.
Each component is self-contained, uses Tailwind CSS for styling, and is designed to be composed together.

---

## 1. Button (`snippet_01_button.jsx`)
A reusable button component with three visual variants.
- Supports `primary` (blue), `secondary` (gray), and `danger` (red) styles
- Accepts `disabled` prop which reduces opacity and blocks interaction
- Used as the base action trigger across all other components like forms and modals

---

## 2. SearchBar (`snippet_02_search_bar.jsx`)
A controlled text input with built-in debounce logic (400ms delay).
- Prevents excessive re-renders or API calls on every keystroke
- Calls `onSearch` callback only after the user stops typing
- Typically placed above a DataTable to filter displayed records

---

## 3. DataTable (`snippet_03_data_table.jsx`)
A dynamic table that renders any columns and row data passed as props.
- `columns` prop is an array of `{ key, label }` objects
- `data` prop is an array of row objects matching column keys
- Horizontally scrollable for wide datasets
- Used together with SearchBar and Pagination for full data management UI

---

## 4. Modal (`snippet_04_modal.jsx`)
An overlay dialog box with a dark backdrop and close behavior.
- Closes on Escape key press or clicking the close (✕) button
- Renders nothing when `isOpen` is false (no DOM bloat)
- Accepts any children — commonly wraps a Form component

---

## 5. Form (`snippet_05_form.jsx`)
A controlled form with two fields (name, email) and inline validation.
- Validates that name is non-empty and email contains `@`
- Shows field-level error messages in red below each input
- Calls `onSubmit` callback only when validation passes
- Designed to be placed inside a Modal or standalone on a page

---

## 6. Sidebar (`snippet_06_sidebar.jsx`)
A vertical navigation sidebar with collapse/expand toggle.
- Collapses to icon-only mode (w-16) or expands to full labels (w-56)
- Highlights the currently active nav item
- Accepts `items` array of `{ label, icon }` objects
- Used as the left panel in DashboardLayout

---

## 7. Toast (`snippet_07_toast.jsx`)
A custom hook that provides a floating notification system.
- Returns `addToast(message, type)` function and a `ToastContainer` component
- Supports `info` (dark), `success` (green), `error` (red) types
- Toasts auto-dismiss after 3 seconds
- Mount `<ToastContainer />` once at the app root, call `addToast` anywhere

---

## 8. Pagination (`snippet_08_pagination.jsx`)
A page navigation component for splitting large datasets across pages.
- Calculates total pages from `total` records and `perPage` count
- Highlights the current active page button
- Disables Prev/Next buttons at boundaries
- Used below a DataTable when data exceeds one page

---

## 9. Card (`snippet_09_card.jsx`)
A stat/info display card for dashboard metrics.
- Shows a `title`, large `value`, an `icon`, and optional `trend` percentage
- Trend shows green upward arrow for positive, red downward for negative
- Designed to be rendered in a grid of 3 columns in the dashboard header

---

## 10. DashboardLayout (`snippet_10_dashboard_layout.jsx`)
A full-page layout shell combining Sidebar and stat Cards.
- Left panel is the collapsible Sidebar with 4 nav items
- Main content area shows a 3-column Card grid at the top
- Accepts `children` for the main content area below the cards
- This is the top-level wrapper for any dashboard page
