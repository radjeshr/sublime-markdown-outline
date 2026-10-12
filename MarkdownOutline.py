# Markdown Outline for Sublime Text — v1.0.0
#
# Progressive drill-down:
# - A global Fold Level is the baseline view.
# - Individual branches can be expanded one level deeper without opening
#   unrelated branches.
# - Individual visible branches can also be collapsed locally.
# - The outline and the main editor stay synchronized.
# - Folding is editor-safe: normal typing does not automatically rebuild folds.
# - MarkdownOutline owns only its own fold regions and leaves unrelated folds alone.

import html
import json
import re

import sublime
import sublime_plugin


VERSION = "1.0.0"
PANEL_NAME = "Markdown Outline"
MANAGED_FOLDS_KEY = "markdown_outline.managed_folds"

# Per Sublime window:
# {
#   window_id: {
#       "source_view_id": int,
#       "sheet_id": int,
#       "original_layout": dict,
#       "collapsed": {view_id: {node_key, ...}},
#       "expanded": {view_id: {node_key, ...}},
#       "fold_level": int | None
#   }
# }
STATE = {}


# ---------------------------------------------------------------------------
# Sublime helpers
# ---------------------------------------------------------------------------

def get_window(window_id):
    for window in sublime.windows():
        if window.id() == window_id:
            return window
    return None


def get_view(window, view_id):
    if not window or view_id is None:
        return None

    for view in window.views(include_transient=True):
        if view.id() == view_id:
            return view

    return None


def get_sheet(window, sheet_id):
    if not window or sheet_id is None:
        return None

    for sheet in window.sheets():
        if sheet.id() == sheet_id:
            return sheet

    return None


def is_markdown(view):
    if not view:
        return False

    filename = view.file_name()
    if filename:
        lower = filename.lower()
        if lower.endswith((".md", ".markdown", ".mdown", ".mkd", ".mkdn")):
            return True

    try:
        return view.match_selector(0, "text.html.markdown")
    except Exception:
        return False


def subl_link(command, args=None):
    """Return a clickable Sublime command URL for an HTML sheet."""
    try:
        return sublime.command_url(command, args)
    except Exception:
        if args:
            url = "subl:{} {}".format(
                command,
                json.dumps(args, separators=(",", ":"))
            )
        else:
            url = "subl:{}".format(command)

        return html.escape(url, quote=True)


# ---------------------------------------------------------------------------
# Markdown model
# ---------------------------------------------------------------------------

def parse_headings(view):
    """
    Parse Markdown ATX headings (# through ######).

    Fenced code blocks using ``` or ~~~ are ignored.
    Returns dictionaries containing: level, row, title.
    """
    text = view.substr(sublime.Region(0, view.size()))
    lines = text.splitlines()

    headings = []
    fence_char = None

    for row, line in enumerate(lines):
        fence_match = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)

        if fence_match:
            char = fence_match.group(1)[0]

            if fence_char is None:
                fence_char = char
            elif fence_char == char:
                fence_char = None

            continue

        if fence_char is not None:
            continue

        match = re.match(r"^\s{0,3}(#{1,6})[ \t]+(.+?)\s*$", line)
        if not match:
            continue

        level = len(match.group(1))
        title = match.group(2).strip()

        # Optional closing hashes: ## Heading ##
        title = re.sub(r"\s+#+\s*$", "", title).strip()

        headings.append({
            "level": level,
            "row": row,
            "title": title,
        })

    return headings


def build_tree(headings):
    """
    Return (parents, children).

    parents[i] is the index of the nearest preceding heading with a lower
    Markdown level, or None for a root node.

    children[i] contains direct structural child indices. This also handles
    documents that skip heading levels, e.g. H1 -> H3.
    """
    parents = [None] * len(headings)
    children = [[] for _ in headings]
    stack = []

    for index, heading in enumerate(headings):
        level = heading["level"]

        while stack and headings[stack[-1]]["level"] >= level:
            stack.pop()

        parent = stack[-1] if stack else None
        parents[index] = parent

        if parent is not None:
            children[parent].append(index)

        stack.append(index)

    return parents, children


def build_node_keys(headings):
    """
    Build stable structural keys for headings.

    Keys are based on the heading's position inside the outline tree rather
    than its line number. Body edits and heading text edits therefore do not
    destroy local expand/collapse state merely because line numbers changed.
    """
    parents, children = build_tree(headings)
    keys = [None] * len(headings)
    child_ordinals = {}

    root_ordinal = 0

    for index in range(len(headings)):
        parent = parents[index]

        if parent is None:
            keys[index] = str(root_ordinal)
            root_ordinal += 1
            continue

        ordinal = child_ordinals.get(parent, 0)
        child_ordinals[parent] = ordinal + 1
        keys[index] = "{}/{}".format(keys[parent], ordinal)

    return keys


def descendant_keys(node_keys, key):
    """Return all structural descendant keys below key."""
    prefix = key + "/"
    return {candidate for candidate in node_keys if candidate.startswith(prefix)}


def heading_index_for_key(node_keys, key):
    try:
        return node_keys.index(str(key))
    except ValueError:
        return None


def visible_heading_indices(
    headings,
    fold_level=None,
    expanded_keys=None,
    collapsed_keys=None,
    node_keys=None
):
    """
    Calculate which headings are visible in the outline.

    The global Fold Level is a baseline. Individual branches can then be
    expanded one structural level deeper without affecting unrelated branches.
    """
    expanded_keys = expanded_keys or set()
    collapsed_keys = collapsed_keys or set()

    parents, _ = build_tree(headings)
    node_keys = node_keys or build_node_keys(headings)

    visible = []
    visible_set = set()

    for index, heading in enumerate(headings):
        parent = parents[index]

        if parent is None:
            if fold_level is None or heading["level"] <= fold_level:
                visible.append(index)
                visible_set.add(index)
            continue

        if parent not in visible_set:
            continue

        parent_key = node_keys[parent]

        if parent_key in collapsed_keys:
            continue

        if fold_level is None:
            show = True
        else:
            show = (
                heading["level"] <= fold_level
                or parent_key in expanded_keys
            )

        if show:
            visible.append(index)
            visible_set.add(index)

    return visible


# ---------------------------------------------------------------------------
# Per-view state
# ---------------------------------------------------------------------------

def current_collapsed(state):
    view_id = state.get("source_view_id")
    collapsed_by_view = state.setdefault("collapsed", {})

    if view_id not in collapsed_by_view:
        collapsed_by_view[view_id] = set()

    return collapsed_by_view[view_id]


def current_expanded(state):
    view_id = state.get("source_view_id")
    expanded_by_view = state.setdefault("expanded", {})

    if view_id not in expanded_by_view:
        expanded_by_view[view_id] = set()

    return expanded_by_view[view_id]


def prune_heading_state(state, headings):
    """Drop stored structural keys that no longer exist in this document."""
    valid_keys = set(build_node_keys(headings))

    collapsed = current_collapsed(state)
    expanded = current_expanded(state)

    collapsed.intersection_update(valid_keys)
    expanded.intersection_update(valid_keys)


# ---------------------------------------------------------------------------
# Editor folding
# ---------------------------------------------------------------------------

def clear_managed_folds(view):
    """
    Unfold only regions previously created by MarkdownOutline.

    This deliberately does NOT call unfold() on the whole document, because
    doing so would destroy folds the user created manually or through another
    Markdown package.
    """
    if not view:
        return

    try:
        regions = view.get_regions(MANAGED_FOLDS_KEY)
    except Exception:
        regions = []

    if regions:
        try:
            view.unfold(regions)
        except Exception:
            # Compatibility fallback.
            for region in regions:
                try:
                    view.unfold(region)
                except Exception:
                    pass

    try:
        view.erase_regions(MANAGED_FOLDS_KEY)
    except Exception:
        pass


def install_managed_folds(view, regions):
    """
    Install the folds owned by MarkdownOutline and remember their live Regions.

    add_regions() keeps the marker Regions synchronized with buffer edits, so
    later explicit tree/fold actions can remove exactly our folds even if line
    numbers have changed in the meantime.
    """
    if not view:
        return

    regions = [
        region for region in regions
        if region is not None and region.end() > region.begin()
    ]

    if not regions:
        try:
            view.erase_regions(MANAGED_FOLDS_KEY)
        except Exception:
            pass
        return

    try:
        view.fold(regions)
    except Exception:
        for region in regions:
            try:
                view.fold(region)
            except Exception as exc:
                print("MarkdownOutline fold error:", exc)

    try:
        # Empty scope/icon => invisible bookkeeping regions.
        view.add_regions(MANAGED_FOLDS_KEY, regions, "", "", 0)
    except Exception as exc:
        print("MarkdownOutline managed-region error:", exc)


def fold_end_before_boundary(view, boundary):
    """
    Return the end of the physical line immediately before `boundary`.

    This lets a fold start on the heading that OWNS the section while keeping
    the final newline before the next visible heading outside the fold.

    Result:
        current heading [folded section...] <visible newline> next heading

    That prevents the systematic N -> N-1 gutter-fold association while also
    preventing visible headings from being concatenated onto one line.
    """
    if boundary <= 0:
        return boundary

    probe = max(0, boundary - 1)

    try:
        return view.line(probe).end()
    except Exception:
        return max(0, boundary - 1)


def section_region(view, headings, index):
    """
    Region after the heading line through the end of that heading's section.
    The heading line itself stays visible.
    """
    heading = headings[index]
    heading_point = view.text_point(heading["row"], 0)

    # Start at the end of the heading text so Sublime associates the native
    # gutter fold marker with THIS heading.
    start = view.line(heading_point).end()

    end = view.size()
    level = heading["level"]

    for next_index in range(index + 1, len(headings)):
        if headings[next_index]["level"] <= level:
            next_point = view.text_point(headings[next_index]["row"], 0)
            boundary = view.line(next_point).begin()
            end = fold_end_before_boundary(view, boundary)
            break

    if end <= start:
        return None

    return sublime.Region(start, end)


def restore_editor_interaction_state(view, viewport, selections):
    """
    Restore the user's visual position after an explicit outline fold action.

    Folding can make Sublime scroll to a previous fold boundary. We restore the
    old viewport. Selections are restored only when they are still visible,
    because restoring a caret inside a folded region would reopen that fold.
    """
    if not view:
        return

    try:
        folded = view.folded_regions()

        def is_hidden(point):
            return any(region.contains(point) for region in folded)

        if selections and all(
            not is_hidden(region.a) and not is_hidden(region.b)
            for region in selections
        ):
            view.sel().clear()
            for region in selections:
                view.sel().add(sublime.Region(region.a, region.b))
    except Exception:
        pass

    def restore_viewport():
        try:
            view.set_viewport_position(viewport, False)
        except Exception:
            pass

    sublime.set_timeout(restore_viewport, 0)


def park_selection_for_folding(view, safe_point):
    """
    Temporarily move the caret to a guaranteed-visible heading before folds
    are rebuilt.

    Sublime may refuse to keep a region folded when the active caret/selection
    is inside that region. That produced the apparent N-1 bug: the previous
    day/section could remain unfolded when the next tree node was opened.

    The original selection is restored afterwards when it remains visible.
    """
    if not view or safe_point is None:
        return

    try:
        point = max(0, min(int(safe_point), view.size()))
        view.sel().clear()
        view.sel().add(sublime.Region(point, point))
    except Exception:
        pass


def apply_editor_state(view, fold_level, expanded_keys, collapsed_keys, focus_key=None):
    """
    Synchronize the main editor after an EXPLICIT outline folding action.

    v0.3.2 rules:
      * every fold is anchored to the heading that owns it;
      * the newline before the next visible heading stays visible;
      * MarkdownOutline removes/rebuilds only folds it owns;
      * normal typing/editing never calls this function;
      * unrelated/manual Sublime folds are left alone.
    """
    if not view or not is_markdown(view):
        return

    headings = parse_headings(view)
    if not headings:
        clear_managed_folds(view)
        return

    node_keys = build_node_keys(headings)
    viewport = view.viewport_position()
    selections = [sublime.Region(region.a, region.b) for region in view.sel()]

    # Remove only our previous folds. Do not nuke the user's other folds.
    clear_managed_folds(view)

    regions = []
    safe_point = None

    if fold_level is not None:
        visible_indices = visible_heading_indices(
            headings,
            fold_level=fold_level,
            expanded_keys=expanded_keys,
            collapsed_keys=collapsed_keys,
            node_keys=node_keys,
        )

        if visible_indices:
            # Prefer the branch the user just clicked as the temporary caret
            # location. Otherwise use the first visible heading.
            focus_index = None
            if focus_key is not None:
                focus_index = heading_index_for_key(node_keys, focus_key)
                if focus_index not in visible_indices:
                    focus_index = None

            if focus_index is None:
                focus_index = visible_indices[0]

            safe_heading = headings[focus_index]
            safe_point = view.text_point(safe_heading["row"], 0)

            # Hide content/headings before the first heading that belongs in
            # the current outline view. This fixes e.g. an H2 that occurs
            # before the first visible H1 while Fold Level 1 is active.
            first_heading = headings[visible_indices[0]]
            first_point = view.text_point(first_heading["row"], 0)
            prefix_end = view.line(first_point).begin()

            if prefix_end > 0:
                prefix_fold_end = fold_end_before_boundary(view, prefix_end)
                if prefix_fold_end > 0:
                    regions.append(sublime.Region(0, prefix_fold_end))

            # Fold only the content AFTER the complete heading line. This
            # preserves the newline, so visible headings never concatenate.
            # The N-1 issue is handled separately by parking the caret outside
            # regions that are about to be folded.
            for visible_pos, index in enumerate(visible_indices):
                heading = headings[index]
                point = view.text_point(heading["row"], 0)

                # Start on the owning heading, but preserve the line break
                # immediately before the next visible heading.
                start = view.line(point).end()

                if visible_pos + 1 < len(visible_indices):
                    next_heading = headings[visible_indices[visible_pos + 1]]
                    next_point = view.text_point(next_heading["row"], 0)
                    boundary = view.line(next_point).begin()
                    end = fold_end_before_boundary(view, boundary)
                else:
                    end = view.size()

                if end > start:
                    regions.append(sublime.Region(start, end))

    else:
        # No global Fold Level: fold only branches explicitly collapsed in
        # the outline. If possible, park the caret on the branch just clicked.
        if focus_key is not None:
            focus_index = heading_index_for_key(node_keys, focus_key)
            if focus_index is not None:
                safe_heading = headings[focus_index]
                safe_point = view.text_point(safe_heading["row"], 0)

        # Each region is tied to the heading that owns it.
        if collapsed_keys:
            parents, _ = build_tree(headings)
            key_to_index = {key: i for i, key in enumerate(node_keys)}
            top_level_collapsed = []

            for key in collapsed_keys:
                index = key_to_index.get(key)
                if index is None:
                    continue

                parent = parents[index]
                ancestor_is_collapsed = False

                while parent is not None:
                    if node_keys[parent] in collapsed_keys:
                        ancestor_is_collapsed = True
                        break
                    parent = parents[parent]

                if not ancestor_is_collapsed:
                    top_level_collapsed.append(index)

            for index in sorted(top_level_collapsed):
                region = section_region(view, headings, index)
                if region:
                    regions.append(region)

    # Critical: move the caret out of regions that are about to be folded.
    # Otherwise Sublime can leave the region containing the old caret open,
    # which looks exactly like the previous (N-1) heading was unfolded.
    if safe_point is None and headings:
        safe_point = view.text_point(headings[0]["row"], 0)

    park_selection_for_folding(view, safe_point)
    install_managed_folds(view, regions)
    restore_editor_interaction_state(view, viewport, selections)


def sync_editor_to_state(window):
    state = STATE.get(window.id()) if window else None
    if not state:
        return

    view = get_view(window, state.get("source_view_id"))
    if not view:
        return

    headings = parse_headings(view)
    prune_heading_state(state, headings)

    focus_key = state.pop("last_action_key", None)

    apply_editor_state(
        view,
        state.get("fold_level"),
        current_expanded(state),
        current_collapsed(state),
        focus_key=focus_key,
    )


# ---------------------------------------------------------------------------
# Outline HTML
# ---------------------------------------------------------------------------

def build_html(window):
    state = STATE.get(window.id())
    if not state:
        return ""

    view = get_view(window, state.get("source_view_id"))
    fold_level = state.get("fold_level")

    fold_label = (
        "Unfolded"
        if fold_level is None
        else "Level {}".format(fold_level)
    )

    toolbar = """
        <div class="toolbar">
            <b>MARKDOWN OUTLINE</b>
            <span class="tools">
                <a href="{fold_menu}" title="Global fold level">Fold: {fold_label} ▾</a>
                &nbsp;&nbsp;
                <a href="{refresh}" title="Refresh">↻</a>
                &nbsp;
                <a href="{expand}" title="Unfold all">＋</a>
                &nbsp;
                <a href="{collapse}" title="Fold to level 1">−</a>
                &nbsp;
                <a href="{close}" title="Close outline">×</a>
            </span>
        </div>
    """.format(
        fold_menu=subl_link("md_outline_fold_menu"),
        fold_label=html.escape(fold_label),
        refresh=subl_link("md_outline_refresh"),
        expand=subl_link("md_outline_expand_all"),
        collapse=subl_link("md_outline_collapse_all"),
        close=subl_link("md_outline_close"),
    )

    css = """
        <style>
            body {
                margin: 0.7rem;
                font-size: 0.95rem;
            }

            .toolbar {
                margin-bottom: 0.8rem;
                padding-bottom: 0.5rem;
            }

            .tools {
                float: right;
            }

            .tools a,
            .heading a {
                text-decoration: none;
            }

            .heading {
                margin-top: 0.15rem;
                margin-bottom: 0.15rem;
                white-space: nowrap;
            }

            .toggle {
                display: inline-block;
                width: 1.2rem;
                text-align: center;
            }

            .empty {
                opacity: 0.65;
                margin-top: 1rem;
            }

            .h1, .h2 {
                font-weight: bold;
            }
        </style>
    """

    if not view:
        return (
            "<html><body>{}{}"
            "<div class='empty'>No source document.</div>"
            "</body></html>"
        ).format(css, toolbar)

    if not is_markdown(view):
        return (
            "<html><body>{}{}"
            "<div class='empty'>Current document is not Markdown.</div>"
            "</body></html>"
        ).format(css, toolbar)

    headings = parse_headings(view)

    if not headings:
        return (
            "<html><body>{}{}"
            "<div class='empty'>No Markdown headings found.</div>"
            "</body></html>"
        ).format(css, toolbar)

    prune_heading_state(state, headings)

    collapsed = current_collapsed(state)
    expanded = current_expanded(state)
    node_keys = build_node_keys(headings)

    visible_indices = visible_heading_indices(
        headings,
        fold_level=fold_level,
        expanded_keys=expanded,
        collapsed_keys=collapsed,
        node_keys=node_keys,
    )
    visible_set = set(visible_indices)

    _, children = build_tree(headings)
    rows = []

    for index in visible_indices:
        heading = headings[index]
        level = heading["level"]
        source_row = heading["row"]
        node_key = node_keys[index]
        title = heading["title"]

        direct_children = children[index]
        has_child_nodes = bool(direct_children)
        has_visible_child = any(
            child_index in visible_set
            for child_index in direct_children
        )

        if has_child_nodes:
            symbol = "▾" if has_visible_child else "▸"

            if has_visible_child:
                action_title = "Collapse this branch"
            else:
                action_title = "Expand this branch one level"

            toggle = """
                <a class="toggle"
                   href="{href}"
                   title="{action_title}">{symbol}</a>
            """.format(
                href=subl_link("md_outline_toggle", {"key": node_key}),
                action_title=action_title,
                symbol=symbol,
            )
        else:
            toggle = '<span class="toggle">·</span>'

        jump = subl_link("md_outline_jump", {"line": source_row})
        indent = (level - 1) * 0.85

        rows.append(
            """
            <div class="heading h{level}" style="padding-left: {indent}rem;">
                {toggle}
                <a href="{jump}" title="Go to line {line}">{title}</a>
            </div>
            """.format(
                level=level,
                indent=indent,
                toggle=toggle,
                jump=jump,
                line=source_row + 1,
                title=html.escape(title),
            )
        )

    body = "\n".join(rows)
    return "<html><body>{}{}{}</body></html>".format(css, toolbar, body)


def update_outline(window):
    if not window:
        return

    state = STATE.get(window.id())
    if not state:
        return

    sheet = get_sheet(window, state.get("sheet_id"))
    if not sheet:
        return

    try:
        sheet.set_contents(build_html(window))
    except Exception as exc:
        print("MarkdownOutline update error:", exc)


def schedule_update(window_id, view_id, delay=180):
    """
    Refresh only the outline HTML.

    Never reapply editor folding from edit/save/activation events. Folding is
    user-driven only; typing must not alter the editor's fold state.
    """
    def do_update():
        window = get_window(window_id)
        if not window:
            return

        state = STATE.get(window_id)
        if not state or state.get("source_view_id") != view_id:
            return

        update_outline(window)

    sublime.set_timeout(do_update, delay)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

class MdOutlineShowCommand(sublime_plugin.WindowCommand):
    def run(self):
        window = self.window
        view = window.active_view()

        if not view:
            sublime.status_message("Markdown Outline: no active document.")
            return

        if not is_markdown(view):
            sublime.message_dialog(
                "Markdown Outline works only with Markdown files."
            )
            return

        window_id = window.id()

        # Already open: switch the outline to the current Markdown file.
        if window_id in STATE:
            STATE[window_id]["source_view_id"] = view.id()
            update_outline(window)
            return

        if window.num_groups() != 1:
            sublime.message_dialog(
                "Markdown Outline currently expects a single editor group.\n\n"
                "Select View > Layout > Single first, then run "
                "'Markdown Outline: Show Right'."
            )
            return

        original_layout = window.layout()

        STATE[window_id] = {
            "source_view_id": view.id(),
            "sheet_id": None,
            "original_layout": original_layout,
            "collapsed": {},
            "expanded": {},
            "fold_level": None,
        }

        # Main editor ~78%, outline ~22%.
        window.set_layout({
            "cols": [0.0, 0.78, 1.0],
            "rows": [0.0, 1.0],
            "cells": [
                [0, 0, 1, 1],
                [1, 0, 2, 1],
            ],
        })

        sheet = window.new_html_sheet(PANEL_NAME, "", group=1)
        STATE[window_id]["sheet_id"] = sheet.id()

        update_outline(window)
        window.focus_view(view)


class MdOutlineCloseCommand(sublime_plugin.WindowCommand):
    def run(self):
        window = self.window
        state = STATE.get(window.id())

        if not state:
            return

        sheet = get_sheet(window, state.get("sheet_id"))
        if sheet:
            try:
                sheet.close()
            except Exception:
                pass

        original_layout = state.get("original_layout")
        del STATE[window.id()]

        if original_layout:
            try:
                window.set_layout(original_layout)
            except Exception as exc:
                print("MarkdownOutline layout restore error:", exc)


class MdOutlineRefreshCommand(sublime_plugin.WindowCommand):
    def run(self):
        update_outline(self.window)


class MdOutlineJumpCommand(sublime_plugin.WindowCommand):
    def run(self, line):
        state = STATE.get(self.window.id())
        if not state:
            return

        view = get_view(self.window, state.get("source_view_id"))
        if not view:
            return

        point = view.text_point(int(line), 0)
        view.sel().clear()
        view.sel().add(sublime.Region(point, point))

        self.window.focus_view(view)
        view.show_at_center(point)


class MdOutlineToggleCommand(sublime_plugin.WindowCommand):
    def run(self, key=None, line=None):
        """
        Toggle one branch without changing the global Fold Level.

        State is stored by structural outline key, not line number. Therefore
        inserting/deleting normal text or editing heading text does not make
        the tree forget which branches were expanded.
        """
        state = STATE.get(self.window.id())
        if not state:
            return

        view = get_view(self.window, state.get("source_view_id"))
        if not view:
            return

        headings = parse_headings(view)
        prune_heading_state(state, headings)

        node_keys = build_node_keys(headings)

        if key is not None:
            index = heading_index_for_key(node_keys, key)
        elif line is not None:
            # Backward-compatible fallback for an old HTML sheet still open
            # while the plugin is hot-reloaded.
            try:
                wanted_row = int(line)
            except Exception:
                wanted_row = -1

            index = next(
                (
                    i for i, heading in enumerate(headings)
                    if heading["row"] == wanted_row
                ),
                None,
            )
        else:
            index = None

        if index is None:
            return

        _, children = build_tree(headings)
        if not children[index]:
            return

        collapsed = current_collapsed(state)
        expanded = current_expanded(state)
        fold_level = state.get("fold_level")

        visible_indices = visible_heading_indices(
            headings,
            fold_level=fold_level,
            expanded_keys=expanded,
            collapsed_keys=collapsed,
            node_keys=node_keys,
        )
        visible_set = set(visible_indices)

        direct_children_visible = any(
            child_index in visible_set
            for child_index in children[index]
        )

        node_key = node_keys[index]
        descendants = descendant_keys(node_keys, node_key)

        if direct_children_visible:
            # Close only this branch and discard deeper local drill-down state.
            collapsed.add(node_key)
            expanded.discard(node_key)
            collapsed.difference_update(descendants)
            expanded.difference_update(descendants)
        else:
            collapsed.discard(node_key)

            if fold_level is not None:
                # Reveal exactly one structural child level.
                expanded.add(node_key)
            else:
                expanded.discard(node_key)

        # Explicit tree folding is allowed to synchronize the main editor.
        # Tell the fold engine which heading is guaranteed to remain visible;
        # it temporarily parks the caret there while folds are rebuilt.
        state["last_action_key"] = node_key
        sync_editor_to_state(self.window)
        update_outline(self.window)


class MdOutlineFoldMenuCommand(sublime_plugin.WindowCommand):
    def run(self):
        items = [
            "Unfold All",
            "Fold Level 1  —  show #",
            "Fold Level 2  —  show # and ##",
            "Fold Level 3  —  show # through ###",
            "Fold Level 4  —  show # through ####",
            "Fold Level 5  —  show # through #####",
            "Fold Level 6  —  show all heading levels",
        ]

        def selected(index):
            if index < 0:
                return

            if index == 0:
                self.window.run_command("md_outline_unfold_all")
            else:
                self.window.run_command(
                    "md_outline_set_fold_level",
                    {"level": index}
                )

        self.window.show_quick_panel(items, selected)


class MdOutlineSetFoldLevelCommand(sublime_plugin.WindowCommand):
    def run(self, level):
        state = STATE.get(self.window.id())
        if not state:
            return

        level = max(1, min(6, int(level)))
        state["fold_level"] = level

        # A new global level starts from a clean baseline for this document.
        current_collapsed(state).clear()
        current_expanded(state).clear()

        sync_editor_to_state(self.window)
        update_outline(self.window)


class MdOutlineUnfoldAllCommand(sublime_plugin.WindowCommand):
    def run(self):
        state = STATE.get(self.window.id())
        if not state:
            return

        state["fold_level"] = None
        current_collapsed(state).clear()
        current_expanded(state).clear()

        view = get_view(self.window, state.get("source_view_id"))
        clear_managed_folds(view)
        update_outline(self.window)


class MdOutlineExpandAllCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.window.run_command("md_outline_unfold_all")


class MdOutlineCollapseAllCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.window.run_command(
            "md_outline_set_fold_level",
            {"level": 1}
        )


# ---------------------------------------------------------------------------
# Event listener
# ---------------------------------------------------------------------------

class MarkdownOutlineListener(sublime_plugin.EventListener):
    def on_activated_async(self, view):
        window = view.window()
        if not window:
            return

        state = STATE.get(window.id())
        if not state:
            return

        try:
            group, _ = window.get_view_index(view)
        except Exception:
            return

        # Group 0 is the real editor; group 1 is the outline HTML sheet.
        if group != 0:
            return

        if not is_markdown(view):
            return

        state["source_view_id"] = view.id()
        schedule_update(window.id(), view.id())

    def on_modified_async(self, view):
        window = view.window()
        if not window:
            return

        state = STATE.get(window.id())
        if not state or state.get("source_view_id") != view.id():
            return

        schedule_update(window.id(), view.id())

    def on_post_save_async(self, view):
        window = view.window()
        if not window:
            return

        state = STATE.get(window.id())
        if not state or state.get("source_view_id") != view.id():
            return

        schedule_update(window.id(), view.id())
