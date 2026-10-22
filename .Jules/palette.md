## 2026-10-22 - Added keyboard accessibility to sidebar navigation
**Learning:** The `.nav` items in the sidebar act as custom interactive elements (buttons) but lacked keyboard support. Implementing `tabindex="0"`, `role="button"`, `:focus-visible` styling, and `keydown` handlers for Enter/Space keys ensures keyboard accessibility without disrupting visual styling or relying on default HTML buttons.
**Action:** Apply this pattern (`tabindex`, `role`, `:focus-visible`, `keydown`) to any custom `div` or `span` acting as a button or interactive element.
