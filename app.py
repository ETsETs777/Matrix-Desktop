import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from tkinter import font as tkfont
 
try:
	from tkinterdnd2 import DND_FILES, TkinterDnD
	DND_AVAILABLE = True
except Exception:
	DND_AVAILABLE = False
import numpy as np
import scipy.linalg as la
import base64
try:
	import cairosvg
	CAIROS, PIL_AVAILABLE = True, False
except Exception:
	CAIROS = False
try:
	from PIL import Image, ImageTk
	PIL_AVAILABLE = True
except Exception:
	if 'PIL_AVAILABLE' not in globals():
		PIL_AVAILABLE = False
import csv
import json
import os

class MatrixApp(tk.Tk if not DND_AVAILABLE else TkinterDnD.Tk):
	def __init__(self):
		super().__init__()
		self.title("Matrix Desktop")
		self.geometry("1000x700")
		self.minsize(960, 640)
		self.style = ttk.Style(self)
		self._init_themes()
		self.theme_var = tk.StringVar(value="dark")
		self._load_prefs()
		self._apply_theme()
		self._ui_font_size = 11
		self._history = []
		self._future = []
		self._build_menu()
		self._build_ui()
		self._build_icons()
		self._autosave_setup()
		self._load_recent()
		self.after(50, self._snap_half_screen)
 
	def _ensure_assets_with_embedded_icons(self):
		assets_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'assets')
		os.makedirs(assets_dir, exist_ok=True)
		return

	def _build_ui(self):
		container = ttk.Frame(self, padding=(12, 12, 12, 12))
		container.pack(fill=tk.BOTH, expand=True)

		header = ttk.Frame(container)
		header.pack(fill=tk.X, pady=(0, 12))
		title = ttk.Label(header, text="Matrix Desktop", style="Title.TLabel")
		title.pack(side=tk.LEFT)
		subtitle = ttk.Label(header, text="Калькулятор матриц", style="Subtitle.TLabel")
		subtitle.pack(side=tk.LEFT, padx=(12, 0))

		toolbar = ttk.Frame(container)
		toolbar.pack(fill=tk.X, pady=(0, 8))
		self._icon_calc = None
		self._icon_clear = None
		btn_calc = ttk.Button(toolbar, text="Вычислить", style="Accent.TButton", command=self.on_calculate)
		btn_calc.pack(side=tk.LEFT, padx=(0, 6))
		btn_clear = ttk.Button(toolbar, text="Очистить", command=self.on_clear)
		btn_clear.pack(side=tk.LEFT)
		zoom_out = ttk.Button(toolbar, text="A-", width=4, command=lambda: self._zoom(-1))
		zoom_out.pack(side=tk.RIGHT)
		zoom_in = ttk.Button(toolbar, text="A+", width=4, command=lambda: self._zoom(1))
		zoom_in.pack(side=tk.RIGHT, padx=(0,6))
		self._add_tooltip(btn_calc, "Выполнить выбранную операцию (Ctrl+Enter)")
		self._add_tooltip(btn_clear, "Очистить поля A, B и результат (Ctrl+L)")
		self._add_tooltip(zoom_in, "Увеличить размер шрифта")
		self._add_tooltip(zoom_out, "Уменьшить размер шрифта")

		tabs = ttk.Notebook(container)
		tabs.pack(fill=tk.X)
		self.op_var = tk.StringVar(value="add")
		cats = {
			"Базовые": [
				("A + B", "add"), ("A - B", "sub"), ("A × B", "mul"), ("A^T", "transposeA"), ("B^T", "transposeB"),
				("det(A)", "detA"), ("det(B)", "detB"), ("rank(A)", "rankA"), ("rank(B)", "rankB"),
				("A^{-1}", "invA"), ("B^{-1}", "invB"), ("Решить Ax=b", "solve")
			],
			"Факторизации": [
				("eig(A)", "eigA"), ("eig(B)", "eigB"), ("SVD(A)", "svdA"), ("SVD(B)", "svdB"),
				("LU(A)", "luA"), ("LU(B)", "luB"), ("QR(A)", "qrA"), ("QR(B)", "qrB"),
				("Cholesky(A)", "cholA"), ("Cholesky(B)", "cholB")
			],
			"Другое": [
				("pinv(A)", "pinvA"), ("pinv(B)", "pinvB"), ("‖A‖ и cond(A)", "normCondA"), ("‖B‖ и cond(B)", "normCondB")
			]
		}
		for name, items in cats.items():
			frame = ttk.Frame(tabs)
			tabs.add(frame, text=name)
			inner = ttk.Frame(frame, padding=(10, 8, 10, 8))
			inner.pack(fill=tk.X)
			for text, val in items:
				rb = ttk.Radiobutton(inner, text=text, variable=self.op_var, value=val, style="Modern.TRadiobutton")
				rb.pack(side=tk.LEFT, padx=6, pady=2)
				self._add_tooltip(rb, f"Операция: {text}")

		mid = ttk.Frame(container)
		mid.pack(fill=tk.BOTH, expand=True, pady=12)

		left = ttk.Labelframe(mid, text="Матрица A", style="Card.TLabelframe", padding=(10, 8, 10, 8))
		left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,6))
		right = ttk.Labelframe(mid, text="Матрица B / вектор b", style="Card.TLabelframe", padding=(10, 8, 10, 8))
		right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(6,0))
		hist = ttk.Labelframe(mid, text="История", style="Card.TLabelframe", padding=(10,8,10,8))
		hist.pack(side=tk.LEFT, fill=tk.Y, padx=(6,0))

		self._build_matrix_editor(left, which="A")
		self._build_matrix_editor(right, which="B")

		self.history_list = tk.Listbox(hist, height=16)
		self.history_list.pack(fill=tk.BOTH, expand=True)
		hbtns = ttk.Frame(hist)
		hbtns.pack(fill=tk.X, pady=(6,0))
		self.btn_hist_to_A = ttk.Button(hbtns, text="Вставить → A", command=lambda: self._history_apply("A"))
		self.btn_hist_to_A.pack(side=tk.LEFT)
		self.btn_hist_to_B = ttk.Button(hbtns, text="Вставить → B", command=lambda: self._history_apply("B"))
		self.btn_hist_to_B.pack(side=tk.LEFT, padx=6)
		self.history_list.bind('<Double-Button-1>', lambda e: self._history_apply("A"))
		self._hist_menu = tk.Menu(self, tearoff=0)
		self._hist_menu.add_command(label="Вставить в A", command=lambda: self._history_apply("A"))
		self._hist_menu.add_command(label="Вставить в B", command=lambda: self._history_apply("B"))
		self._hist_menu.add_separator()
		self._hist_menu.add_command(label="Копировать", command=self._history_copy)
		self.history_list.bind('<Button-3>', self._history_context)
		self._set_placeholder(self.textA, "Пример:\n1 2 3\n4 5 6")
		self._set_placeholder(self.textB, "Пример:\n9 8 7\n6 5 4")
		self._add_tooltip(self.textA, "Матрица A: числа разделяйте пробелом/запятой/точкой с запятой")
		self._add_tooltip(self.textB, "Матрица B или вектор b для Ax=b")

		btns = ttk.Frame(container)
		btns.pack(fill=tk.X)
		self.calc_btn = ttk.Button(btns, text="Вычислить", style="Accent.TButton", command=self.on_calculate)
		self.calc_btn.pack(side=tk.LEFT)
		self.clear_btn = ttk.Button(btns, text="Очистить", command=self.on_clear)
		self.clear_btn.pack(side=tk.LEFT, padx=8)
		info = ttk.Label(btns, text="Ctrl+Enter — вычислить, Ctrl+L — очистить", style="Help.TLabel")
		info.pack(side=tk.RIGHT)

		out = ttk.Labelframe(container, text="Результат", style="Card.TLabelframe", padding=(10, 8, 10, 8))
		out.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
		self.result = self._make_scrolled_text(out)
		self.result.configure(state=tk.DISABLED)

		notes_box = ttk.Labelframe(container, text="Заметки", style="Card.TLabelframe", padding=(10, 8, 10, 8))
		notes_box.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
		self.notes = self._make_scrolled_text(notes_box)

		self.status = ttk.Label(self, text="Готово", anchor=tk.W, style="Status.TLabel")
		self.status.pack(fill=tk.X, side=tk.BOTTOM)

		self.bind_all("<Control-Return>", lambda e: self.on_calculate())
		self.bind_all("<Control-Return>", lambda e: self.on_calculate())
		self.bind_all("<Control-l>", lambda e: self.on_clear())
		self.bind_all("<Control-z>", lambda e: self._undo())
		self.bind_all("<Control-y>", lambda e: self._redo())

		self._apply_text_colors()

	def _make_scrolled_text(self, parent):
		outer = ttk.Frame(parent)
		outer.pack(fill=tk.BOTH, expand=True)
		txt = tk.Text(outer, wrap=tk.NONE, height=14, relief=tk.FLAT, bd=0)
		vx = ttk.Scrollbar(outer, orient=tk.HORIZONTAL, command=txt.xview)
		vy = ttk.Scrollbar(outer, orient=tk.VERTICAL, command=txt.yview)
		txt.configure(xscrollcommand=vx.set, yscrollcommand=vy.set, font=self._mono_font())
		txt.grid(row=0, column=0, sticky="nsew")
		vy.grid(row=0, column=1, sticky="ns")
		vx.grid(row=1, column=0, sticky="ew")
		outer.columnconfigure(0, weight=1)
		outer.rowconfigure(0, weight=1)
		self._attach_focus_animation(txt)
		return txt

	def _build_matrix_editor(self, parent, which="A"):
		wrap = ttk.Frame(parent)
		wrap.pack(fill=tk.BOTH, expand=True)
		toolbar = ttk.Frame(wrap)
		toolbar.pack(fill=tk.X)
		add_row = ttk.Button(toolbar, text="+R", width=4, command=lambda: self._grid_add_row(which))
		add_row.pack(side=tk.LEFT)
		add_col = ttk.Button(toolbar, text="+C", width=4, command=lambda: self._grid_add_col(which))
		add_col.pack(side=tk.LEFT, padx=4)
		del_row = ttk.Button(toolbar, text="-R", width=4, command=lambda: self._grid_del_row(which))
		del_row.pack(side=tk.LEFT)
		del_col = ttk.Button(toolbar, text="-C", width=4, command=lambda: self._grid_del_col(which))
		del_col.pack(side=tk.LEFT, padx=4)
		mode = ttk.Button(toolbar, text="Текст", width=8, command=lambda: self._toggle_editor_mode(which))
		mode.pack(side=tk.RIGHT)

		container = ttk.Frame(wrap)
		container.pack(fill=tk.BOTH, expand=True)
		tree = ttk.Treeview(container, show="headings", selectmode="browse")
		tree.grid(row=0, column=0, sticky="nsew")
		vs = ttk.Scrollbar(container, orient=tk.VERTICAL, command=tree.yview)
		vs.grid(row=0, column=1, sticky="ns")
		hs = ttk.Scrollbar(container, orient=tk.HORIZONTAL, command=tree.xview)
		hs.grid(row=1, column=0, sticky="ew")
		tree.configure(yscroll=vs.set, xscroll=hs.set)
		container.columnconfigure(0, weight=1)
		container.rowconfigure(0, weight=1)

		editor = tk.Entry(container, relief=tk.FLAT)
		editor.place_forget()

		cols = [f"c{i+1}" for i in range(3)]
		tree["columns"] = cols
		for i, col in enumerate(cols):
			tree.heading(col, text=str(i+1))
			tree.column(col, width=60, anchor=tk.CENTER)
		for _ in range(3):
			tree.insert("", tk.END, values=["0" for _ in cols])

		def begin_edit(event):
			region = tree.identify("region", event.x, event.y)
			if region != "cell":
				return
			rowid = tree.identify_row(event.y)
			colid = tree.identify_column(event.x)
			if not rowid or not colid:
				return
			ci = int(colid[1:]) - 1
			x, y, w, h = tree.bbox(rowid, colid)
			val = tree.set(rowid, cols[ci])
			editor.place(x=x+1, y=y+1, width=w-2, height=h-2)
			editor.delete(0, tk.END)
			editor.insert(0, val)
			editor.focus_set()
			editor.selection_range(0, tk.END)
			editor._rowid = rowid
			editor._ci = ci

		def commit_edit(event=None):
			rowid = getattr(editor, "_rowid", None)
			ci = getattr(editor, "_ci", None)
			if rowid is None or ci is None:
				editor.place_forget()
				return
			text = editor.get().strip()
			ok = True
			try:
				float(text)
			except Exception:
				ok = False
				text = "0"
				self._flash_tree_cell(tree, rowid, cols[ci])
			tree.set(rowid, cols[ci], text)
			editor.place_forget()
			if ok:
				self._sync_grid_to_text(which)

		def cancel_edit(event=None):
			editor.place_forget()

		tree.bind("<Double-1>", begin_edit)
		editor.bind("<Return>", commit_edit)
		editor.bind("<Escape>", cancel_edit)
		editor.bind("<FocusOut>", commit_edit)

		if which == "A":
			self.treeA = tree
			self.textA = self._make_scrolled_text(parent)
			self.textA.pack_forget()
			self._grid_mode_A = True
			if DND_AVAILABLE:
				self.drop_target_register(DND_FILES)
				self.textA.drop_target_register(DND_FILES)
				self.textA.dnd_bind('<<Drop>>', lambda e: self._on_drop_file(e, target='A'))
		else:
			self.treeB = tree
			self.textB = self._make_scrolled_text(parent)
			self.textB.pack_forget()
			self._grid_mode_B = True
			if DND_AVAILABLE:
				self.drop_target_register(DND_FILES)
				self.textB.drop_target_register(DND_FILES)
				self.textB.dnd_bind('<<Drop>>', lambda e: self._on_drop_file(e, target='B'))

	def _toggle_editor_mode(self, which):
		if which == "A":
			self._grid_mode_A = not self._grid_mode_A
			if self._grid_mode_A:
				self.textA.pack_forget()
				self.treeA.master.pack(fill=tk.BOTH, expand=True)
				self._text_to_grid(which)
			else:
				self.treeA.master.pack_forget()
				self.textA.pack(fill=tk.BOTH, expand=True)
				self._grid_to_text(which)
		else:
			self._grid_mode_B = not self._grid_mode_B
			if self._grid_mode_B:
				self.textB.pack_forget()
				self.treeB.master.pack(fill=tk.BOTH, expand=True)
				self._text_to_grid(which)
			else:
				self.treeB.master.pack_forget()
				self.textB.pack(fill=tk.BOTH, expand=True)
				self._grid_to_text(which)

	def _grid_add_row(self, which):
		tree = self.treeA if which == "A" else self.treeB
		cols = tree["columns"]
		tree.insert("", tk.END, values=["0" for _ in cols])
		self._sync_grid_to_text(which)

	def _grid_del_row(self, which):
		tree = self.treeA if which == "A" else self.treeB
		cur = tree.selection()
		if not cur:
			return
		tree.delete(cur[0])
		self._sync_grid_to_text(which)

	def _grid_add_col(self, which):
		tree = self.treeA if which == "A" else self.treeB
		cols = list(tree["columns"]) + [f"c{len(tree['columns'])+1}"]
		tree["columns"] = cols
		for i, col in enumerate(cols):
			tree.heading(col, text=str(i+1))
			tree.column(col, width=60, anchor=tk.CENTER)
		for iid in tree.get_children(""):
			vals = list(tree.item(iid, "values"))
			vals.append("0")
			tree.item(iid, values=vals)
		self._sync_grid_to_text(which)

	def _grid_del_col(self, which):
		tree = self.treeA if which == "A" else self.treeB
		cols = list(tree["columns"])
		if len(cols) <= 1:
			return
		cols.pop()
		tree["columns"] = cols
		for i, col in enumerate(cols):
			tree.heading(col, text=str(i+1))
			tree.column(col, width=60, anchor=tk.CENTER)
		for iid in tree.get_children(""):
			vals = list(tree.item(iid, "values"))
			if vals:
				vals.pop()
				tree.item(iid, values=vals)
		self._sync_grid_to_text(which)

	def _flash_tree_cell(self, tree, rowid, colname):
		orig = tree.tag_has("error")
		vals = list(tree.item(rowid, "values"))
		idx = list(tree["columns"]).index(colname)
		vals[idx] = vals[idx]
		tree.item(rowid, values=vals, tags=("error",))
		tree.tag_configure("error", background="#FEE2E2")
		self.after(600, lambda: tree.item(rowid, values=vals, tags=()))

	def _sync_grid_to_text(self, which):
		tree = self.treeA if which == "A" else self.treeB
		lines = []
		for iid in tree.get_children(""):
			vals = tree.item(iid, "values")
			lines.append(" ".join(str(v) for v in vals))
		text = "\n".join(lines)
		if which == "A":
			self.textA.delete("1.0", tk.END)
			self.textA.insert("1.0", text)
		else:
			self.textB.delete("1.0", tk.END)
			self.textB.insert("1.0", text)

	def _text_to_grid(self, which):
		tree = self.treeA if which == "A" else self.treeB
		text = self.textA.get("1.0", tk.END) if which == "A" else self.textB.get("1.0", tk.END)
		rows = [r.strip() for r in text.strip().splitlines() if r.strip()]
		if not rows:
			return
		data = []
		for r in rows:
			parts = [p for p in r.replace(";", " ").replace(",", " ").split() if p]
			data.append(parts)
		cols = max((len(r) for r in data), default=0)
		if cols == 0:
			return
		colnames = [f"c{i+1}" for i in range(cols)]
		tree["columns"] = colnames
		for i, col in enumerate(colnames):
			tree.heading(col, text=str(i+1))
			tree.column(col, width=60, anchor=tk.CENTER)
		for iid in tree.get_children(""):
			tree.delete(iid)
		for row in data:
			filled = row + ["0"] * (cols - len(row))
			tree.insert("", tk.END, values=filled)

	def _mono_font(self):
		return tkfont.Font(family="Consolas", size=self._ui_font_size)

	def _zoom(self, delta):
		self._ui_font_size = max(8, min(28, self._ui_font_size + delta))
		for txt in getattr(self, "_all_text_widgets", []):
			txt.configure(font=self._mono_font())
		if hasattr(self, "status"):
			self.status.configure(text=f"Размер шрифта: {self._ui_font_size}")

	def _set_placeholder(self, widget, text):
		def on_focus_in(e):
			if widget.get("1.0", "end-1c") == text:
				widget.delete("1.0", tk.END)
				widget.configure(fg=self.style.lookup("TLabel", "foreground"))
		def on_focus_out(e):
			if not widget.get("1.0", "end-1c").strip():
				widget.insert("1.0", text)
				widget.configure(fg=self.style.lookup("Help.TLabel", "foreground"))
		widget.insert("1.0", text)
		widget.configure(fg=self.style.lookup("Help.TLabel", "foreground"))
		widget.bind("<FocusIn>", on_focus_in)
		widget.bind("<FocusOut>", on_focus_out)

	def _add_tooltip(self, widget, text):
		tip = tk.Toplevel(widget)
		tip.withdraw()
		tip.overrideredirect(True)
		lbl = ttk.Label(tip, text=text, style="Help.TLabel", padding=(8,4))
		lbl.pack()
		def show(event):
			tip.deiconify()
			tip.lift()
			x = widget.winfo_rootx() + 10
			y = widget.winfo_rooty() + widget.winfo_height() + 6
			tip.geometry(f"+{x}+{y}")
		def hide(event):
			tip.withdraw()
		widget.bind("<Enter>", show)
		widget.bind("<Leave>", hide)

	def _build_menu(self):
		menubar = tk.Menu(self)
		filem = tk.Menu(menubar, tearoff=0)
		filem.add_command(label="Импорт A из CSV", command=lambda: self._import_csv(target="A"))
		filem.add_command(label="Импорт B из CSV", command=lambda: self._import_csv(target="B"))
		filem.add_command(label="Импорт JSON", command=self._import_json)
		filem.add_separator()
		filem.add_command(label="Экспорт A в CSV", command=lambda: self._export_csv(source="A"))
		filem.add_command(label="Экспорт B в CSV", command=lambda: self._export_csv(source="B"))
		filem.add_command(label="Экспорт результата в CSV", command=lambda: self._export_csv(source="R"))
		filem.add_command(label="Экспорт JSON", command=self._export_json)
		filem.add_separator()
		filem.add_command(label="Экспорт результата в LaTeX", command=self._export_latex)
		filem.add_command(label="Копировать результат", command=self._copy_result)
		filem.add_command(label="Копировать результат как таблицу", command=self._copy_result_tsv)
		filem.add_separator()
		self._recent_menu = tk.Menu(filem, tearoff=0)
		filem.add_cascade(label="Последние", menu=self._recent_menu)
		filem.add_separator()
		filem.add_command(label="Выход", command=self.destroy)
		menubar.add_cascade(label="Файл", menu=filem)

		matm = tk.Menu(menubar, tearoff=0)
		matm.add_command(label="Сгенерировать A...", command=lambda: self._generate_matrix("A"))
		matm.add_command(label="Сгенерировать B...", command=lambda: self._generate_matrix("B"))
		matm.add_separator()
		matm.add_command(label="RREF(A) с шагами", command=lambda: self._do_rref("A"))
		matm.add_command(label="RREF(B) с шагами", command=lambda: self._do_rref("B"))
		menubar.add_cascade(label="Матрицы", menu=matm)

		editm = tk.Menu(menubar, tearoff=0)
		editm.add_command(label="Отменить (Ctrl+Z)", command=self._undo)
		editm.add_command(label="Повторить (Ctrl+Y)", command=self._redo)
		menubar.add_cascade(label="Правка", menu=editm)

		view = tk.Menu(menubar, tearoff=0)
		view.add_radiobutton(label="Светлая тема", value="light", variable=self.theme_var, command=self._on_toggle_theme)
		view.add_radiobutton(label="Тёмная тема", value="dark", variable=self.theme_var, command=self._on_toggle_theme)
		view.add_radiobutton(label="Контрастная тема", value="contrast", variable=self.theme_var, command=self._on_toggle_theme)
		menubar.add_cascade(label="Вид", menu=view)
		self.config(menu=menubar)

	def _on_toggle_theme(self):
		self._apply_theme()
		self._save_prefs()

	def _init_themes(self):
		light = {
			"bg": "#F5F7FB",
			"surface": "#FFFFFF",
			"text": "#1F2937",
			"muted": "#6B7280",
			"primary": "#2563EB",
			"primary_hover": "#1D4ED8",
			"border": "#E5E7EB",
			"accent_text": "#FFFFFF"
		}
		dark = {
			"bg": "#0F172A",
			"surface": "#111827",
			"text": "#E5E7EB",
			"muted": "#9CA3AF",
			"primary": "#60A5FA",
			"primary_hover": "#3B82F6",
			"border": "#1F2937",
			"accent_text": "#0B1220"
		}
		contrast = {
			"bg": "#000000",
			"surface": "#000000",
			"text": "#FFFFFF",
			"muted": "#FFD700",
			"primary": "#FFFF00",
			"primary_hover": "#FFD700",
			"border": "#FFFFFF",
			"accent_text": "#000000"
		}
		if "matrix-light" not in self.style.theme_names():
			self.style.theme_create("matrix-light", parent="clam", settings={
				"TFrame": {"configure": {"background": light["bg"]}},
				"TLabelframe": {"configure": {"background": light["surface"], "foreground": light["text"], "bordercolor": light["border"]}},
				"TLabelframe.Label": {"configure": {"background": light["surface"], "foreground": light["muted"], "font": ("Segoe UI", 10, "bold")}},
				"TLabel": {"configure": {"background": light["bg"], "foreground": light["text"]}},
				"Title.TLabel": {"configure": {"background": light["bg"], "foreground": light["text"], "font": ("Segoe UI Semibold", 18)}},
				"Subtitle.TLabel": {"configure": {"background": light["bg"], "foreground": light["muted"], "font": ("Segoe UI", 11)}},
				"Help.TLabel": {"configure": {"background": light["bg"], "foreground": light["muted"]}},
				"Status.TLabel": {"configure": {"background": light["surface"], "foreground": light["muted"], "padding": (10, 6)}},
				"TButton": {"configure": {"background": light["surface"], "foreground": light["text"], "padding": (12, 8)}, "map": {"background": [("active", light["border"])], "foreground": [("disabled", light["muted"])]}},
				"Accent.TButton": {"configure": {"background": light["primary"], "foreground": light["accent_text"]}, "map": {"background": [("active", light["primary_hover"])]}},
				"TRadiobutton": {"configure": {"background": light["bg"], "foreground": light["text"]}},
				"Modern.TRadiobutton": {"configure": {"background": light["bg"], "foreground": light["text"]}}
			})
		if "matrix-dark" not in self.style.theme_names():
			self.style.theme_create("matrix-dark", parent="clam", settings={
				"TFrame": {"configure": {"background": dark["bg"]}},
				"TLabelframe": {"configure": {"background": dark["surface"], "foreground": dark["text"], "bordercolor": dark["border"]}},
				"TLabelframe.Label": {"configure": {"background": dark["surface"], "foreground": dark["muted"], "font": ("Segoe UI", 10, "bold")}},
				"TLabel": {"configure": {"background": dark["bg"], "foreground": dark["text"]}},
				"Title.TLabel": {"configure": {"background": dark["bg"], "foreground": dark["text"], "font": ("Segoe UI Semibold", 18)}},
				"Subtitle.TLabel": {"configure": {"background": dark["bg"], "foreground": dark["muted"], "font": ("Segoe UI", 11)}},
				"Help.TLabel": {"configure": {"background": dark["bg"], "foreground": dark["muted"]}},
				"Status.TLabel": {"configure": {"background": dark["surface"], "foreground": dark["muted"], "padding": (10, 6)}},
				"TButton": {"configure": {"background": dark["surface"], "foreground": dark["text"], "padding": (12, 8)}, "map": {"background": [("active", dark["border"])], "foreground": [("disabled", dark["muted"])]}},
				"Accent.TButton": {"configure": {"background": dark["primary"], "foreground": dark["accent_text"]}, "map": {"background": [("active", dark["primary_hover"])]}},
				"TRadiobutton": {"configure": {"background": dark["bg"], "foreground": dark["text"]}},
				"Modern.TRadiobutton": {"configure": {"background": dark["bg"], "foreground": dark["text"]}}
			})
		if "matrix-contrast" not in self.style.theme_names():
			self.style.theme_create("matrix-contrast", parent="clam", settings={
				"TFrame": {"configure": {"background": contrast["bg"]}},
				"TLabelframe": {"configure": {"background": contrast["surface"], "foreground": contrast["text"], "bordercolor": contrast["border"]}},
				"TLabelframe.Label": {"configure": {"background": contrast["surface"], "foreground": contrast["muted"], "font": ("Segoe UI", 11, "bold")}},
				"TLabel": {"configure": {"background": contrast["bg"], "foreground": contrast["text"]}},
				"Title.TLabel": {"configure": {"background": contrast["bg"], "foreground": contrast["text"], "font": ("Segoe UI Semibold", 18)}},
				"Subtitle.TLabel": {"configure": {"background": contrast["bg"], "foreground": contrast["muted"], "font": ("Segoe UI", 11)}},
				"Help.TLabel": {"configure": {"background": contrast["bg"], "foreground": contrast["muted"]}},
				"Status.TLabel": {"configure": {"background": contrast["surface"], "foreground": contrast["muted"], "padding": (10, 6)}},
				"TButton": {"configure": {"background": contrast["surface"], "foreground": contrast["text"], "padding": (12, 8)}, "map": {"background": [("active", contrast["border"])], "foreground": [("disabled", contrast["muted"])]}},
				"Accent.TButton": {"configure": {"background": contrast["primary"], "foreground": contrast["accent_text"]}, "map": {"background": [("active", contrast["primary_hover"])]}},
				"TRadiobutton": {"configure": {"background": contrast["bg"], "foreground": contrast["text"]}},
				"Modern.TRadiobutton": {"configure": {"background": contrast["bg"], "foreground": contrast["text"]}}
			})

	def _apply_theme(self):
		chosen = self.theme_var.get()
		if chosen == "dark":
			self.style.theme_use("matrix-dark")
		elif chosen == "contrast":
			self.style.theme_use("matrix-contrast")
		else:
			self.style.theme_use("matrix-light")
		bg = self.style.lookup("TFrame", "background")
		self.configure(bg=bg)
		if hasattr(self, "status"):
			self.status.configure(text=f"Тема: {self.theme_var.get()}")
		self._apply_text_colors()

	def _apply_text_colors(self):
		is_dark = self.theme_var.get() != "light"
		if is_dark:
			bg = "#0B1220"
			fg = "#E5E7EB"
			cursor = "#60A5FA"
			select = "#1F3B73"
			border = "#1F2937"
		else:
			bg = "#FFFFFF"
			fg = "#1F2937"
			cursor = "#2563EB"
			select = "#DBEAFE"
			border = "#E5E7EB"
		for txt in getattr(self, "_all_text_widgets", []):
			txt.configure(bg=bg, fg=fg, insertbackground=cursor, selectbackground=select, highlightthickness=1, highlightbackground=border, highlightcolor=border)
		if not hasattr(self, "_all_text_widgets"):
			self._all_text_widgets = []
		widgets = []
		for name in ("textA", "textB", "result"):
			if hasattr(self, name):
				widgets.append(getattr(self, name))
		self._all_text_widgets = widgets
		for txt in self._all_text_widgets:
			txt.configure(bg=bg, fg=fg, insertbackground=cursor, selectbackground=select, highlightthickness=2, highlightbackground=border, highlightcolor=border)

	def _attach_focus_animation(self, widget):
		def animate(to_color, steps=8, interval=15):
			from_colors = widget.cget("highlightbackground")
			def hex_to_rgb(h):
				h = h.lstrip('#')
				return tuple(int(h[i:i+2], 16) for i in (0,2,4))
			def rgb_to_hex(rgb):
				return '#%02x%02x%02x' % rgb
			c0 = hex_to_rgb(from_colors) if isinstance(from_colors, str) and from_colors.startswith('#') else (31,41,55)
			c1 = hex_to_rgb(to_color)
			for i in range(1, steps+1):
				mix = tuple(int(c0[j] + (c1[j]-c0[j]) * i/steps) for j in range(3))
				widget.after(i*interval, lambda m=mix: widget.configure(highlightbackground=rgb_to_hex(m), highlightcolor=rgb_to_hex(m)))
		def on_focus_in(e):
			animate('#3B82F6')
		def on_focus_out(e):
			base = '#1F2937' if self.theme_var.get() != 'light' else '#E5E7EB'
			animate(base)
		widget.bind('<FocusIn>', on_focus_in)
		widget.bind('<FocusOut>', on_focus_out)

	def _snap_half_screen(self):
		try:
			self.state('zoomed')
		except Exception:
			pass

	def _build_icons(self):
		self._ensure_assets_with_embedded_icons()
		def load_png(path, size=(18,18)):
			try:
				if PIL_AVAILABLE:
					im = Image.open(path).convert('RGBA')
					if size:
						im = im.resize(size, Image.LANCZOS)
					return ImageTk.PhotoImage(im)
				return tk.PhotoImage(file=path)
			except Exception:
				return None
		def load_svg(path, size=(18,18)):
			if not CAIROS:
				return None
			try:
				png_bytes = cairosvg.svg2png(url=path, output_width=size[0], output_height=size[1])
				if PIL_AVAILABLE:
					from io import BytesIO
					im = Image.open(BytesIO(png_bytes)).convert('RGBA')
					return ImageTk.PhotoImage(im)
				tmp = os.path.join(os.path.dirname(path), '_tmp_icon.png')
				with open(tmp, 'wb') as f:
					f.write(png_bytes)
				img = tk.PhotoImage(file=tmp)
				os.remove(tmp)
				return img
			except Exception:
				return None
		assets_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'assets')
		calc_png_path = os.path.join(assets_dir, 'calc.png')
		clear_png_path = os.path.join(assets_dir, 'clear.png')
		calc_svg_path = os.path.join(assets_dir, 'calc.svg')
		clear_svg_path = os.path.join(assets_dir, 'clear.svg')
		self._icon_calc = load_png(calc_png_path) or load_svg(calc_svg_path) or None
		self._icon_clear = load_png(clear_png_path) or load_svg(clear_svg_path) or None
		if hasattr(self, 'calc_btn'):
			if self._icon_calc:
				self.calc_btn.configure(image=self._icon_calc, compound=tk.LEFT)
		if hasattr(self, 'clear_btn'):
			if self._icon_clear:
				self.clear_btn.configure(image=self._icon_clear, compound=tk.LEFT)

	def _autosave_setup(self):
		self._autosave_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'last_state.json')
		self.after(2000, self._autosave_tick)
		self._restore_last_state()

	def _restore_last_state(self):
		try:
			with open(self._autosave_path, 'r', encoding='utf-8') as f:
				obj = json.load(f)
			self.textA.delete('1.0', tk.END)
			self.textA.insert('1.0', obj.get('A', ''))
			self.textB.delete('1.0', tk.END)
			self.textB.insert('1.0', obj.get('B', ''))
			self._set_result(obj.get('R', ''))
		except Exception:
			pass

	def _autosave_tick(self):
		try:
			obj = {
				'A': self.textA.get('1.0', tk.END),
				'B': self.textB.get('1.0', tk.END),
				'R': self.result.get('1.0', tk.END)
			}
			with open(self._autosave_path, 'w', encoding='utf-8') as f:
				json.dump(obj, f, ensure_ascii=False)
		except Exception:
			pass
		self.after(2000, self._autosave_tick)

	def _save_prefs(self):
		prefs = {"theme": self.theme_var.get()}
		try:
			with open(self._prefs_path(), "w", encoding="utf-8") as f:
				json.dump(prefs, f)
		except Exception:
			pass

	def _load_prefs(self):
		try:
			with open(self._prefs_path(), "r", encoding="utf-8") as f:
				prefs = json.load(f)
			self.theme_var.set(prefs.get("theme", "dark"))
		except Exception:
			self.theme_var.set("dark")

	def _prefs_path(self):
		return os.path.join(os.path.abspath(os.path.dirname(__file__)), "settings.json")

	def _recent_path(self):
		return os.path.join(os.path.abspath(os.path.dirname(__file__)), "recent.json")

	def _load_recent(self):
		try:
			with open(self._recent_path(), 'r', encoding='utf-8') as f:
				self._recent = json.load(f)
		except Exception:
			self._recent = []
		self._rebuild_recent_menu()

	def _save_recent(self):
		try:
			with open(self._recent_path(), 'w', encoding='utf-8') as f:
				json.dump(self._recent[:10], f, ensure_ascii=False, indent=2)
		except Exception:
			pass

	def _add_recent(self, path):
		if not path:
			return
		if not isinstance(path, str):
			return
		if path in getattr(self, '_recent', []):
			self._recent.remove(path)
		self._recent.insert(0, path)
		self._save_recent()
		self._rebuild_recent_menu()

	def _rebuild_recent_menu(self):
		self._recent_menu.delete(0, tk.END)
		for p in getattr(self, '_recent', [])[:10]:
			self._recent_menu.add_command(label=p, command=lambda q=p: self._open_recent(q))

	def _open_recent(self, path):
		if not os.path.exists(path):
			return
		if path.lower().endswith('.csv'):
			self._open_recent_csv(path)
		elif path.lower().endswith('.json'):
			self._open_recent_json(path)

	def _open_recent_csv(self, path):
		rows = []
		with open(path, newline="", encoding="utf-8") as f:
			data = f.read()
			try:
				dialect = csv.Sniffer().sniff(data)
				reader = csv.reader(data.splitlines(), dialect)
			except Exception:
				reader = csv.reader(data.splitlines(), delimiter=",")
			for r in reader:
				if len(r) == 0:
					continue
				rows.append(" ".join(v.strip() for v in r))
		text = "\n".join(rows)
		self.textA.delete("1.0", tk.END)
		self.textA.insert("1.0", text)

	def _open_recent_json(self, path):
		with open(path, "r", encoding="utf-8") as f:
			obj = json.load(f)
		if isinstance(obj, dict):
			if "A" in obj:
				self.textA.delete("1.0", tk.END)
				self.textA.insert("1.0", self._format_matrix(np.array(obj["A"], dtype=float)))
			if "B" in obj:
				self.textB.delete("1.0", tk.END)
				self.textB.insert("1.0", self._format_matrix(np.array(obj["B"], dtype=float)))

	def _import_json(self):
		path = filedialog.askopenfilename(title="Импорт JSON", filetypes=[("JSON", "*.json"), ("All files", "*.*")])
		if not path:
			return
		with open(path, "r", encoding="utf-8") as f:
			obj = json.load(f)
		self._add_recent(path)
		if isinstance(obj, dict):
			if "A" in obj:
				self.textA.delete("1.0", tk.END)
				self.textA.insert("1.0", self._format_matrix(np.array(obj["A"], dtype=float)))
			if "B" in obj:
				self.textB.delete("1.0", tk.END)
				self.textB.insert("1.0", self._format_matrix(np.array(obj["B"], dtype=float)))
			if "R" in obj:
				self._set_result(self._format_matrix(np.array(obj["R"], dtype=float)))
		if hasattr(self, "status"):
			self.status.configure(text="Импорт JSON выполнен")

	def _export_json(self):
		def parse_text(text):
			rows = [r.strip() for r in text.strip().splitlines() if r.strip()]
			if not rows:
				return []
			data = []
			for r in rows:
				parts = [p for p in r.replace(";", " ").replace(",", " ").split() if p]
				data.append([float(p) for p in parts])
			return data
		obj = {
			"A": parse_text(self.textA.get("1.0", tk.END)),
			"B": parse_text(self.textB.get("1.0", tk.END)),
			"R": parse_text(self.result.get("1.0", tk.END))
		}
		path = filedialog.asksaveasfilename(title="Экспорт JSON", defaultextension=".json", filetypes=[("JSON", "*.json")])
		if not path:
			return
		with open(path, "w", encoding="utf-8") as f:
			json.dump(obj, f, ensure_ascii=False, indent=2)
		if hasattr(self, "status"):
			self.status.configure(text="Экспорт JSON выполнен")

	def _copy_result(self):
		text = self.result.get("1.0", tk.END).strip()
		if not text:
			return
		self._history_add(text)
		self.clipboard_clear()
		self.clipboard_append(text)
		if hasattr(self, "status"):
			self.status.configure(text="Скопировано в буфер обмена")

	def _copy_result_tsv(self):
		text = self.result.get("1.0", tk.END).strip()
		if not text:
			return
		lines = [l.strip("[] ") for l in text.splitlines() if l.strip()]
		rows = []
		for l in lines:
			parts = [p.strip() for p in l.split(";") if p.strip()]
			rows.append("\t".join(parts))
		tsv = "\n".join(rows)
		self.clipboard_clear()
		self.clipboard_append(tsv)
		if hasattr(self, "status"):
			self.status.configure(text="Скопировано как таблица (TSV)")

	def _text_to_matrix_str(self, which):
		if which == "A":
			return self.textA.get("1.0", tk.END)
		if which == "B":
			return self.textB.get("1.0", tk.END)
		return self.result.get("1.0", tk.END)

	def _import_csv(self, target="A"):
		path = filedialog.askopenfilename(title="Импорт CSV", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
		if not path:
			return
		rows = []
		with open(path, newline="", encoding="utf-8") as f:
			data = f.read()
			try:
				dialect = csv.Sniffer().sniff(data)
				reader = csv.reader(data.splitlines(), dialect)
			except Exception:
				reader = csv.reader(data.splitlines(), delimiter=",")
			for r in reader:
				if len(r) == 0:
					continue
				rows.append(" ".join(v.strip() for v in r))
		text = "\n".join(rows)
		self._add_recent(path)
		if target == "A":
			self.textA.delete("1.0", tk.END)
			self.textA.insert("1.0", text)
		else:
			self.textB.delete("1.0", tk.END)
			self.textB.insert("1.0", text)
		if hasattr(self, "status"):
			self.status.configure(text=f"Импортировано в {target}")

	def _export_csv(self, source="A"):
		if source == "A":
			text = self.textA.get("1.0", tk.END).strip()
		elif source == "B":
			text = self.textB.get("1.0", tk.END).strip()
		else:
			text = self.result.get("1.0", tk.END).strip()
		if not text:
			return
		path = filedialog.asksaveasfilename(title="Экспорт CSV", defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
		if not path:
			return
		with open(path, "w", newline="", encoding="utf-8") as f:
			writer = csv.writer(f)
			for line in text.splitlines():
				parts = [p for p in line.replace(";", " ").replace(",", " ").split() if p]
				writer.writerow(parts)
		if hasattr(self, "status"):
			self.status.configure(text="Экспортировано в CSV")

	def _export_latex(self):
		text = self.result.get("1.0", tk.END).strip()
		if not text:
			return
		self._history_add(text)
		lines = [l.strip() for l in text.splitlines() if l.strip()]
		rows = []
		for l in lines:
			l = l.strip("[]")
			parts = [p.strip() for p in l.split(";") if p.strip()]
			rows.append(" \\ ".join(parts))
		latex = "\\begin{bmatrix}\n" + " \\\n".join(rows) + "\n\\end{bmatrix}"
		self.clipboard_clear()
		self.clipboard_append(latex)
		path = filedialog.asksaveasfilename(title="Экспорт LaTeX", defaultextension=".tex", filetypes=[("TeX", "*.tex")])
		if path:
			with open(path, "w", encoding="utf-8") as f:
				f.write(latex)
		if hasattr(self, "status"):
			self.status.configure(text="LaTeX скопирован и сохранён")

	def _generate_matrix(self, which):
		kind = simpledialog.askstring("Генератор", "Тип: identity|random|diag")
		if not kind:
			return
		n = simpledialog.askinteger("Размер", "Число строк", minvalue=1, maxvalue=500)
		m = simpledialog.askinteger("Размер", "Число столбцов", minvalue=1, maxvalue=500)
		if not n or not m:
			return
		M = None
		if kind.lower().startswith("iden"):
			k = min(n, m)
			M = np.zeros((n, m))
			for i in range(k):
				M[i, i] = 1.0
		elif kind.lower().startswith("rand"):
			M = np.random.default_rng().normal(0, 1, size=(n, m))
		elif kind.lower().startswith("diag"):
			k = min(n, m)
			M = np.zeros((n, m))
			for i in range(k):
				val = simpledialog.askfloat("Диагональ", f"Элемент d[{i+1}]")
				M[i, i] = 0.0 if val is None else float(val)
		else:
			return
		text = self._format_matrix(M)
		if which == "A":
			self.textA.delete("1.0", tk.END)
			self.textA.insert("1.0", text)
		else:
			self.textB.delete("1.0", tk.END)
			self.textB.insert("1.0", text)
		if hasattr(self, "status"):
			self.status.configure(text=f"Сгенерирована {which}")

	def _do_rref(self, which):
		try:
			M = self._parse_matrix(self._text_to_matrix_str(which))
		except Exception as e:
			messagebox.showerror("Ошибка ввода", str(e))
			return
		if M is None:
			return
		text = self._rref_steps_text(M)
		self._set_result(text)
		self._history_add(text)
		if hasattr(self, "status"):
			self.status.configure(text=f"RREF({which}) выполнено")

	def _rref_steps_text(self, A):
		A = A.astype(float)
		rows, cols = A.shape
		R = A.copy()
		lines = []
		r = 0
		for c in range(cols):
			if r >= rows:
				break
			pivot = None
			mx = 0.0
			for i in range(r, rows):
				v = abs(R[i, c])
				if v > mx + 1e-12:
					mx = v
					pivot = i
			if pivot is None or abs(R[pivot, c]) < 1e-12:
				continue
			if pivot != r:
				R[[r, pivot], :] = R[[pivot, r], :]
				lines.append(f"swap R{r+1} ↔ R{pivot+1}\n" + self._format_matrix(R))
			val = R[r, c]
			R[r, :] = R[r, :] / val
			lines.append(f"R{r+1} := R{r+1}/{val:g}\n" + self._format_matrix(R))
			for i in range(rows):
				if i == r:
					continue
				fact = R[i, c]
				if abs(fact) < 1e-12:
					continue
				R[i, :] = R[i, :] - fact * R[r, :]
				lines.append(f"R{i+1} := R{i+1} - ({fact:g})*R{r+1}\n" + self._format_matrix(R))
			r += 1
			if r >= rows:
				break
		return "\n\n".join(lines) if lines else self._format_matrix(R)

	def _history_add(self, text):
		if not text:
			return
		lines = text.strip().splitlines()
		preview = lines[0] if lines else text.strip()
		if len(lines) > 1:
			preview += f" (+{len(lines)-1})"
		self.history_list.insert(tk.END, preview)
		self._history_payload = getattr(self, '_history_payload', [])
		self._history_payload.append(text)

	def _history_apply(self, target):
		idx = self.history_list.curselection()
		if not idx:
			return
		text = self._history_payload[idx[0]] if 0 <= idx[0] < len(self._history_payload) else ""
		if not text:
			return
		if target == 'A':
			self.textA.delete('1.0', tk.END)
			self.textA.insert('1.0', text)
			self._text_to_grid('A')
		else:
			self.textB.delete('1.0', tk.END)
			self.textB.insert('1.0', text)
			self._text_to_grid('B')

	def _history_copy(self):
		idx = self.history_list.curselection()
		if not idx:
			return
		text = self._history_payload[idx[0]] if 0 <= idx[0] < len(self._history_payload) else ""
		if not text:
			return
		self.clipboard_clear()
		self.clipboard_append(text)
		if hasattr(self, "status"):
			self.status.configure(text="История: скопировано")

	def _history_context(self, event):
		try:
			self.history_list.selection_clear(0, tk.END)
			self.history_list.selection_set(self.history_list.nearest(event.y))
			self._hist_menu.tk_popup(event.x_root, event.y_root)
		finally:
			self._hist_menu.grab_release()

	def _on_drop_file(self, event, target='A'):
		try:
			path = event.data.strip().strip('{}')
			if path.lower().endswith('.csv'):
				rows = []
				with open(path, newline="", encoding="utf-8") as f:
					data = f.read()
					try:
						dialect = csv.Sniffer().sniff(data)
						reader = csv.reader(data.splitlines(), dialect)
					except Exception:
						reader = csv.reader(data.splitlines(), delimiter=',')
					for r in reader:
						if len(r) == 0:
							continue
						rows.append(' '.join(v.strip() for v in r))
				text = '\n'.join(rows)
			elif path.lower().endswith('.json'):
				with open(path, 'r', encoding='utf-8') as f:
					obj = json.load(f)
					if isinstance(obj, dict) and target in ('A','B'):
						text = self._format_matrix(np.array(obj.get(target, []), dtype=float))
					else:
						text = ''
			else:
				return
			if target == 'A':
				self.textA.delete('1.0', tk.END)
				self.textA.insert('1.0', text)
				self._text_to_grid('A')
			else:
				self.textB.delete('1.0', tk.END)
				self.textB.insert('1.0', text)
				self._text_to_grid('B')
			self._add_recent(path)
		except Exception:
			pass

	def on_clear(self):
		self._push_history()
		self.textA.delete("1.0", tk.END)
		self.textB.delete("1.0", tk.END)
		self._set_result("")
		if hasattr(self, "status"):
			self.status.configure(text="Очищено")

	def _parse_matrix(self, s):
		rows = [r.strip() for r in s.strip().splitlines() if r.strip()]
		if not rows:
			return None
			
		data = []
		for r in rows:
			parts = [p for p in r.replace(";", " ").replace(",", " ").split() if p]
			row = []
			for p in parts:
				row.append(float(p))
			data.append(row)
		
		widths = {len(row) for row in data}
		if len(widths) != 1:
			raise ValueError("Неверная форма: строки имеют разную длину")
		return np.array(data, dtype=float)

	def _format_matrix(self, M):
		if M.ndim == 1:
			return "[" + "; ".join(f"{x:g}" for x in M) + "]"
		rows = ["[" + "; ".join(f"{v:g}" for v in row) + "]" for row in M]
		return "\n".join(rows)

	def _set_result(self, text):
		self.result.configure(state=tk.NORMAL)
		self.result.delete("1.0", tk.END)
		self.result.insert("1.0", text)
		self.result.configure(state=tk.DISABLED)
		if hasattr(self, "status"):
			self.status.configure(text="Готово")

	def _snapshot(self):
		return {
			"A": self.textA.get("1.0", tk.END),
			"B": self.textB.get("1.0", tk.END),
			"R": self.result.get("1.0", tk.END)
		}

	def _restore(self, snap):
		self.textA.delete("1.0", tk.END)
		self.textA.insert("1.0", snap.get("A", ""))
		self.textB.delete("1.0", tk.END)
		self.textB.insert("1.0", snap.get("B", ""))
		self._set_result(snap.get("R", ""))

	def _push_history(self):
		self._history.append(self._snapshot())
		self._future.clear()

	def _undo(self):
		if not self._history:
			return
		cur = self._snapshot()
		snap = self._history.pop()
		self._future.append(cur)
		self._restore(snap)
		if hasattr(self, "status"):
			self.status.configure(text="Отмена")

	def _redo(self):
		if not self._future:
			return
		cur = self._snapshot()
		snap = self._future.pop()
		self._history.append(cur)
		self._restore(snap)
		if hasattr(self, "status"):
			self.status.configure(text="Повтор")

	def on_calculate(self):
		try:
			A = self._parse_matrix(self.textA.get("1.0", tk.END))
			B_or_b = self._parse_matrix(self.textB.get("1.0", tk.END))
		except Exception as e:
			messagebox.showerror("Ошибка ввода", str(e))
			return

		op = self.op_var.get()
		self._push_history()
		try:
			if op in ("add", "sub", "mul"):
				if A is None or B_or_b is None:
					raise ValueError("Нужно ввести A и B")
				if op == "add":
					res = A + B_or_b
				elif op == "sub":
					res = A - B_or_b
				else:
					res = A @ B_or_b
				self._set_result(self._format_matrix(res))
				if hasattr(self, "status"):
					self.status.configure(text="Выполнено: операция над матрицами")
				self._history_add(self._format_matrix(res))
				return

			if op == "transposeA":
				if A is None:
					raise ValueError("Нужно ввести A")
				self._set_result(self._format_matrix(A.T))
				if hasattr(self, "status"):
					self.status.configure(text="Выполнено: A^T")
				self._history_add(self._format_matrix(A.T))
				return
			if op == "transposeB":
				if B_or_b is None:
					raise ValueError("Нужно ввести B")
				self._set_result(self._format_matrix(B_or_b.T))
				if hasattr(self, "status"):
					self.status.configure(text="Выполнено: B^T")
				self._history_add(self._format_matrix(B_or_b.T))
				return

			if op == "detA":
				if A is None:
					raise ValueError("Нужно ввести A")
				val = float(np.linalg.det(A))
				self._set_result(f"det(A) = {val:g}")
				if hasattr(self, "status"):
					self.status.configure(text="Выполнено: det(A)")
				self._history_add(f"det(A) = {val:g}")
				return
			if op == "detB":
				if B_or_b is None:
					raise ValueError("Нужно ввести B")
				val = float(np.linalg.det(B_or_b))
				self._set_result(f"det(B) = {val:g}")
				if hasattr(self, "status"):
					self.status.configure(text="Выполнено: det(B)")
				self._history_add(f"det(B) = {val:g}")
				return

			if op == "rankA":
				if A is None:
					raise ValueError("Нужно ввести A")
				val = int(np.linalg.matrix_rank(A))
				self._set_result(f"rank(A) = {val}")
				if hasattr(self, "status"):
					self.status.configure(text="Выполнено: rank(A)")
				self._history_add(f"rank(A) = {val}")
				return
			if op == "rankB":
				if B_or_b is None:
					raise ValueError("Нужно ввести B")
				val = int(np.linalg.matrix_rank(B_or_b))
				self._set_result(f"rank(B) = {val}")
				if hasattr(self, "status"):
					self.status.configure(text="Выполнено: rank(B)")
				self._history_add(f"rank(B) = {val}")
				return

			if op == "invA":
				if A is None:
					raise ValueError("Нужно ввести A")
				res = np.linalg.inv(A)
				self._set_result(self._format_matrix(res))
				if hasattr(self, "status"):
					self.status.configure(text="Выполнено: A^{-1}")
				self._history_add(self._format_matrix(res))
				return
			if op == "invB":
				if B_or_b is None:
					raise ValueError("Нужно ввести B")
				res = np.linalg.inv(B_or_b)
				self._set_result(self._format_matrix(res))
				if hasattr(self, "status"):
					self.status.configure(text="Выполнено: B^{-1}")
				self._history_add(self._format_matrix(res))
				return

			if op == "solve":
				if A is None or B_or_b is None:
					raise ValueError("Нужно ввести A и вектор b в правом поле")
				b = B_or_b
				if b.ndim == 2 and b.shape[1] == 1:
					b = b.ravel()
				elif b.ndim == 2 and b.shape[0] == 1:
					b = b.ravel()
				elif b.ndim > 1 and 1 not in b.shape:
					raise ValueError("b должен быть вектором (одна строка или один столбец)")
				res = np.linalg.solve(A, b)
				self._set_result(self._format_matrix(res))
				if hasattr(self, "status"):
					self.status.configure(text="Выполнено: Ax=b")
				self._history_add(self._format_matrix(res))
				return

			if op in ("eigA", "eigB"):
				M = A if op == "eigA" else B_or_b
				name = "A" if op == "eigA" else "B"
				if M is None:
					raise ValueError(f"Нужно ввести {name}")
				w, v = np.linalg.eig(M)
				text = "Собственные значения:\n" + self._format_matrix(w) + "\n\nСобственные векторы (по столбцам):\n" + self._format_matrix(v)
				self._set_result(text)
				if hasattr(self, "status"):
					self.status.configure(text=f"Выполнено: eig({name})")
				self._history_add(text)
				return

			if op in ("svdA", "svdB"):
				M = A if op == "svdA" else B_or_b
				name = "A" if op == "svdA" else "B"
				if M is None:
					raise ValueError(f"Нужно ввести {name}")
				U, s, Vt = np.linalg.svd(M, full_matrices=False)
				text = "U:\n" + self._format_matrix(U) + "\n\nΣ:\n" + self._format_matrix(np.diag(s)) + "\n\nV^T:\n" + self._format_matrix(Vt)
				self._set_result(text)
				if hasattr(self, "status"):
					self.status.configure(text=f"Выполнено: SVD({name})")
				self._history_add(text)
				return

			if op in ("luA", "luB"):
				M = A if op == "luA" else B_or_b
				name = "A" if op == "luA" else "B"
				if M is None:
					raise ValueError(f"Нужно ввести {name}")
				P, L, U = la.lu(M)
				text = "P:\n" + self._format_matrix(P) + "\n\nL:\n" + self._format_matrix(L) + "\n\nU:\n" + self._format_matrix(U)
				self._set_result(text)
				if hasattr(self, "status"):
					self.status.configure(text=f"Выполнено: LU({name})")
				self._history_add(text)
				return

			if op in ("qrA", "qrB"):
				M = A if op == "qrA" else B_or_b
				name = "A" if op == "qrA" else "B"
				if M is None:
					raise ValueError(f"Нужно ввести {name}")
				Q, R = np.linalg.qr(M)
				text = "Q:\n" + self._format_matrix(Q) + "\n\nR:\n" + self._format_matrix(R)
				self._set_result(text)
				if hasattr(self, "status"):
					self.status.configure(text=f"Выполнено: QR({name})")
				self._history_add(text)
				return

			if op in ("cholA", "cholB"):
				M = A if op == "cholA" else B_or_b
				name = "A" if op == "cholA" else "B"
				if M is None:
					raise ValueError(f"Нужно ввести {name}")
				L = np.linalg.cholesky(M)
				self._set_result("L:\n" + self._format_matrix(L))
				if hasattr(self, "status"):
					self.status.configure(text=f"Выполнено: Cholesky({name})")
				self._history_add("L:\n" + self._format_matrix(L))
				return

			if op in ("pinvA", "pinvB"):
				M = A if op == "pinvA" else B_or_b
				name = "A" if op == "pinvA" else "B"
				if M is None:
					raise ValueError(f"Нужно ввести {name}")
				res = np.linalg.pinv(M)
				self._set_result(self._format_matrix(res))
				if hasattr(self, "status"):
					self.status.configure(text=f"Выполнено: pinv({name})")
				self._history_add(self._format_matrix(res))
				return

			if op in ("normCondA", "normCondB"):
				M = A if op == "normCondA" else B_or_b
				name = "A" if op == "normCondA" else "B"
				if M is None:
					raise ValueError(f"Нужно ввести {name}")
				n1 = la.norm(M, 1)
				n2 = la.norm(M, 2)
				ninf = la.norm(M, np.inf)
				text = f"‖{name}‖_1 = {n1:g}\n‖{name}‖_2 = {n2:g}\n‖{name}‖_∞ = {ninf:g}"
				try:
					c2 = np.linalg.cond(M)
					text += f"\ncond_2({name}) = {c2:g}"
				except Exception:
					pass
				self._set_result(text)
				if hasattr(self, "status"):
					self.status.configure(text=f"Выполнено: нормы/cond({name})")
				self._history_add(text)
				return

			raise ValueError("Неизвестная операция")
		except np.linalg.LinAlgError as e:
			self._set_result(f"Линейная алгебра: {str(e)}")
		except Exception as e:
			self._set_result(f"Ошибка: {str(e)}")

if __name__ == "__main__":
	app = MatrixApp()
	app.mainloop()
