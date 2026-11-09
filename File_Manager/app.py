"""File Manager — a Streamlit UI for basic file operations (CRUD).

Create, read, rename, append to, overwrite and delete text files.
All files live inside a single `workspace/` folder so the app can never
touch anything outside it.
"""

from datetime import datetime
from pathlib import Path

import streamlit as st

WORKSPACE = Path("workspace")
WORKSPACE.mkdir(exist_ok=True)

st.set_page_config(page_title="File Manager", page_icon="🗂️", layout="wide")

st.markdown(
    """
    <style>
      .block-container { padding-top: 2rem; max-width: 1100px; }
      div[data-testid="stMetricValue"] { font-size: 1.6rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- helpers ----------
def safe_path(name: str) -> Path | None:
    """Return a path inside WORKSPACE, or None if the name is invalid."""
    name = name.strip()
    if not name or name in {".", ".."}:
        return None
    target = (WORKSPACE / name).resolve()
    if target.parent != WORKSPACE.resolve():  # blocks ../ and subfolders
        return None
    return target


def list_files() -> list[Path]:
    return sorted(p for p in WORKSPACE.iterdir() if p.is_file())


def file_picker(label: str, key: str) -> Path | None:
    files = list_files()
    if not files:
        st.info("No files yet. Create one in the **Create** tab.")
        return None
    choice = st.selectbox(label, [f.name for f in files], key=key)
    return WORKSPACE / choice


def flash(kind: str, message: str) -> None:
    """Show a message after st.rerun()."""
    st.session_state["flash"] = (kind, message)


# ---------- header ----------
st.title("🗂️ File Manager")
st.caption("Create, read, update and delete text files — all inside a safe `workspace/` folder.")

if "flash" in st.session_state:
    kind, message = st.session_state.pop("flash")
    getattr(st, kind)(message)

files = list_files()
total_size = sum(f.stat().st_size for f in files)
c1, c2 = st.columns(2)
c1.metric("Files", len(files))
c2.metric("Total size", f"{total_size / 1024:.1f} KB")

# ---------- sidebar ----------
with st.sidebar:
    st.header("Workspace")
    if files:
        for f in files:
            modified = datetime.fromtimestamp(f.stat().st_mtime).strftime("%d %b, %H:%M")
            st.markdown(f"📄 **{f.name}**  \n<small>{f.stat().st_size} bytes · {modified}</small>",
                        unsafe_allow_html=True)
    else:
        st.write("Empty.")

tab_create, tab_read, tab_update, tab_delete = st.tabs(["Create", "Read", "Update", "Delete"])

# ---------- create ----------
with tab_create:
    with st.form("create_form", clear_on_submit=True):
        name = st.text_input("File name", placeholder="notes.txt")
        content = st.text_area("Content", height=200)
        submitted = st.form_submit_button("Create file", type="primary")
    if submitted:
        path = safe_path(name)
        if path is None:
            st.error("Enter a valid file name (no slashes or folders).")
        elif path.exists():
            st.error(f"`{path.name}` already exists. Pick another name or update it.")
        else:
            path.write_text(content, encoding="utf-8")
            flash("success", f"Created `{path.name}`.")
            st.rerun()

# ---------- read ----------
with tab_read:
    path = file_picker("Choose a file", key="read_pick")
    if path:
        text = path.read_text(encoding="utf-8", errors="replace")
        st.text_area("Content", text, height=300, disabled=True, key=f"view_{path.name}_{len(text)}")
        st.download_button("Download", text, file_name=path.name)

# ---------- update ----------
with tab_update:
    path = file_picker("Choose a file", key="update_pick")
    if path:
        action = st.radio("Action", ["Append text", "Overwrite content", "Rename"], horizontal=True)

        if action == "Append text":
            extra = st.text_area("Text to append", key="append_text")
            if st.button("Append", type="primary"):
                if not extra.strip():
                    st.warning("Nothing to append.")
                else:
                    with open(path, "a", encoding="utf-8") as fs:
                        fs.write("\n" + extra)
                    flash("success", f"Appended to `{path.name}`.")
                    st.rerun()

        elif action == "Overwrite content":
            current = path.read_text(encoding="utf-8", errors="replace")
            new_text = st.text_area("Content", current, height=250, key=f"edit_{path.name}")
            if st.button("Save changes", type="primary"):
                path.write_text(new_text, encoding="utf-8")
                flash("success", f"Saved `{path.name}`.")
                st.rerun()

        else:
            new_name = st.text_input("New name", value=path.name, key="rename_input")
            if st.button("Rename", type="primary"):
                new_path = safe_path(new_name)
                if new_path is None:
                    st.error("Enter a valid file name.")
                elif new_path.exists():
                    st.error(f"`{new_path.name}` already exists.")
                else:
                    path.rename(new_path)
                    flash("success", f"Renamed to `{new_path.name}`.")
                    st.rerun()

# ---------- delete ----------
with tab_delete:
    path = file_picker("Choose a file to delete", key="delete_pick")
    if path:
        confirm = st.checkbox(f"Yes, permanently delete `{path.name}`")
        if st.button("Delete file", type="primary", disabled=not confirm):
            path.unlink()
            flash("success", f"Deleted `{path.name}`.")
            st.rerun()