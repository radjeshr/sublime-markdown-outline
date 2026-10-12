# Installation and Usage

## What is Markdown Outline?

Markdown Outline is a lightweight Sublime Text plugin that opens a clickable Markdown heading tree on the right side of the editor.

It uses standard ATX Markdown headings:

```markdown
# Level 1
## Level 2
### Level 3
```

## Installation

### Option 1 — Install the `.sublime-package` release

1. Download `MarkdownOutline.sublime-package` from the latest GitHub release.
2. In Sublime Text, choose **Preferences → Browse Packages…**.
3. Go one folder up from `Packages` to the Sublime Text data directory.
4. Open the folder:

```text
Installed Packages
```

5. Close Sublime Text completely.
6. Copy the downloaded file into that folder and make sure the filename is:

```text
MarkdownOutline.sublime-package
```

On Windows the final path normally looks like:

```text
C:\Users\<your-user-name>\AppData\Roaming\Sublime Text\Installed Packages\MarkdownOutline.sublime-package
```

7. If you used an older development version, remove or rename these files from `Packages\User\`:

```text
MarkdownOutline.py
MarkdownOutline.sublime-commands
```

8. Start Sublime Text again.
9. Open a Markdown file.
10. Press `Ctrl+Shift+P`.
11. Run:

```text
Markdown Outline: Show Right
```

### Option 2 — Install from the repository source

1. In Sublime Text, choose **Preferences → Browse Packages…**.
2. Close Sublime Text.
3. Create a folder named:

```text
MarkdownOutline
```

inside the Sublime Text `Packages` folder.
4. Copy the repository contents into that folder.

The result should look like:

```text
Packages\
└── MarkdownOutline\
    ├── MarkdownOutline.py
    ├── Default.sublime-commands
    ├── Main.sublime-menu
    ├── README.md
    └── ...
```

5. Remove or rename any older development copies from:

```text
Packages\User\MarkdownOutline.py
Packages\User\MarkdownOutline.sublime-commands
```

6. Start Sublime Text.
7. Open a Markdown file.
8. Press `Ctrl+Shift+P`.
9. Run:

```text
Markdown Outline: Show Right
```

## How to use it

The toolbar looks roughly like this:

```text
MARKDOWN OUTLINE    Fold: Level 1 ▾    ↻   +   −   ×
```

### Controls

| Control | Action |
|---|---|
| `Fold: Level N ▾` | Select the global fold level |
| `↻` | Refresh the outline |
| `+` | Unfold everything |
| `−` | Fold to Level 1 |
| `×` | Close the outline |
| `▸ / ▾` | Expand or collapse only that branch |
| Heading text | Jump to that heading in the editor |

## Fold levels

The selected Fold Level acts as the global baseline.

For example:

- **Fold Level 1** shows only `#` headings.
- **Fold Level 2** shows `#` and `##`.
- **Fold Level 3** shows `#`, `##`, and `###`.
- And so on through Level 6.

## Progressive drill-down

Suppose the document contains:

```markdown
# October 2026

## Saturday, October 10, 2026
### Mail
### Tasks

## Sunday, October 11, 2026
### Mail
### Tasks

## Monday, October 12, 2026
### Mail
### Tasks
```

With **Fold Level 1**, only `October 2026` is visible as part of the global baseline.

Click the triangle next to `October 2026` and only that branch opens one level deeper.

Then click the triangle next to `Sunday, October 11, 2026` and only Sunday opens further.

Other branches remain exactly as they were.

## Editing behavior

Normal typing and editing do not automatically rebuild or close your folds.

The outline can refresh after a document edit, but editor folding changes only after an explicit outline or fold command.

## Troubleshooting

### The commands do not appear

Check that the plugin is installed either as:

```text
Installed Packages\MarkdownOutline.sublime-package
```

or as:

```text
Packages\MarkdownOutline\
```

Then restart Sublime Text completely.

### Duplicate commands or strange behavior

Remove old development copies from:

```text
Packages\User\MarkdownOutline.py
Packages\User\MarkdownOutline.sublime-commands
```

### The outline asks for a Single Layout

Choose:

```text
View → Layout → Single
```

Then run:

```text
Markdown Outline: Show Right
```

again.

### A heading does not appear

Markdown Outline currently parses ATX-style headings:

```markdown
# Heading
## Heading
### Heading
```

Setext-style headings are not currently supported:

```markdown
Heading
-------
```
