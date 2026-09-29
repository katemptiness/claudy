# macOS — left to do

On 2026-09-29 the whole project was reviewed and fixed from Linux, and the
macOS changes were then checked on a Mac (macOS 26.7). The click-through
strip around Claudy, the focus a click on him took, and screen changes are
fixed since. What remains is smaller. Delete this file once it is done, and
move anything lasting into `CLAUDE.md`.

- **Settings form.**
  - `form_h = 878` is summed by hand, and the popup block is copy-pasted
    seven times.
  - Lay the form out top-down on a flipped document view. Add one choice
    helper that falls back to the setting's own default, for example
    `Settings.fields()[name].default`.
- **Warp.** "Open Claude Code" only opens a tab; there is no documented way
  to run a command in it. The README says so. If this should work,
  consider a launch configuration.
- **Bubble redraws** (optional). The Linux bubble redraws only when its
  text, typing or fade changes; the macOS one redraws every frame while
  shown.
