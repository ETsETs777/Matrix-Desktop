import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from tkinter import font as tkfont
import numpy as np
import csv
import json
import os

class MatrixApp(tk.Tk):
	def __init__(self):
		super().__init__()
		self.title("Matrix Desktop")
		self.geometry("1000x700")
		self.minsize(960, 640)
		self.style = ttk.Style(self)
		self._init_themes()
		self.dark_mode = tk.BooleanVar(value=True)
		self._load_prefs()
		self._apply_theme()
		self._build_menu()
		self._build_ui()

	def _build_ui(self):
		container = ttk.Frame(self, padding=(12, 12, 12, 12))
		container.pack(fill=tk.BOTH, expand=True)

		header = ttk.Frame(container)
		header.pack(fill=tk.X, pady=(0, 12))
		title = ttk.Label(header, text="Matrix Desktop", style="Title.TLabel")
		title.pack(side=tk.LEFT)
		subtitle = ttk.Label(header, text="Калькулятор матриц", style="Subtitle.TLabel")
		subtitle.pack(side=tk.LEFT, padx=(12, 0))

		top = ttk.Labelframe(container, text="Операции", padding=(10, 8, 10, 8))
		top.pack(fill=tk.X)
		self.op_var = tk.StringVar(value="add")
		ops = [
			("A + B", "add"),
			("A - B", "sub"),
			("A × B", "mul"),
			("A^T", "transposeA"),
			("B^T", "transposeB"),
			("det(A)", "detA"),
			("det(B)", "detB"),
			("rank(A)", "rankA"),
			("rank(B)", "rankB"),
			("A^{-1}", "invA"),
			("B^{-1}", "invB"),
			("Решить Ax=b", "solve")
		]
		for text, val in ops:
			ttk.Radiobutton(top, text=text, variable=self.op_var, value=val, style="Modern.TRadiobutton").pack(side=tk.LEFT, padx=6, pady=2)

		mid = ttk.Frame(container)
		mid.pack(fill=tk.BOTH, expand=True, pady=12)

		left = ttk.Labelframe(mid, text="Матрица A", padding=(10, 8, 10, 8))
		left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,6))
		right = ttk.Labelframe(mid, text="Матрица B / вектор b", padding=(10, 8, 10, 8))
		right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(6,0))

		self.textA = self._make_scrolled_text(left)
		self.textB = self._make_scrolled_text(right)

		btns = ttk.Frame(container)
		btns.pack(fill=tk.X)
		self.calc_btn = ttk.Button(btns, text="Вычислить", style="Accent.TButton", command=self.on_calculate)
		self.calc_btn.pack(side=tk.LEFT)
		self.clear_btn = ttk.Button(btns, text="Очистить", command=self.on_clear)
		self.clear_btn.pack(side=tk.LEFT, padx=8)
		info = ttk.Label(btns, text="Ctrl+Enter — вычислить, Ctrl+L — очистить", style="Help.TLabel")
		info.pack(side=tk.RIGHT)

		out = ttk.Labelframe(container, text="Результат", padding=(10, 8, 10, 8))
		out.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
		self.result = self._make_scrolled_text(out)
		self.result.configure(state=tk.DISABLED)

		self.status = ttk.Label(self, text="Готово", anchor=tk.W, style="Status.TLabel")
		self.status.pack(fill=tk.X, side=tk.BOTTOM)

		self.bind_all("<Control-Return>", lambda e: self.on_calculate())
		self.bind_all("<Control-Return>", lambda e: self.on_calculate())
		self.bind_all("<Control-l>", lambda e: self.on_clear())

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
		return txt

	def _mono_font(self):
		return tkfont.Font(family="Consolas", size=11)

	def _build_menu(self):
		menubar = tk.Menu(self)
		filem = tk.Menu(menubar, tearoff=0)
		filem.add_command(label="Импорт A из CSV", command=lambda: self._import_csv(target="A"))
		filem.add_command(label="Импорт B из CSV", command=lambda: self._import_csv(target="B"))
		filem.add_separator()
		filem.add_command(label="Экспорт A в CSV", command=lambda: self._export_csv(source="A"))
		filem.add_command(label="Экспорт B в CSV", command=lambda: self._export_csv(source="B"))
		filem.add_command(label="Экспорт результата в CSV", command=lambda: self._export_csv(source="R"))
		filem.add_separator()
		filem.add_command(label="Экспорт результата в LaTeX", command=self._export_latex)
		filem.add_command(label="Копировать результат", command=self._copy_result)
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

		view = tk.Menu(menubar, tearoff=0)
		view.add_checkbutton(label="Тёмная тема", onvalue=True, offvalue=False, variable=self.dark_mode, command=self._on_toggle_theme)
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

	def _apply_theme(self):
		self.style.theme_use("matrix-dark" if self.dark_mode.get() else "matrix-light")
		bg = self.style.lookup("TFrame", "background")
		self.configure(bg=bg)
		if hasattr(self, "status"):
			self.status.configure(text="Тёмная тема" if self.dark_mode.get() else "Светлая тема")
		self._apply_text_colors()

	def _apply_text_colors(self):
		is_dark = self.dark_mode.get()
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
			txt.configure(bg=bg, fg=fg, insertbackground=cursor, selectbackground=select, highlightthickness=1, highlightbackground=border, highlightcolor=border)

	def _save_prefs(self):
		prefs = {"dark_mode": self.dark_mode.get()}
		try:
			with open(self._prefs_path(), "w", encoding="utf-8") as f:
				json.dump(prefs, f)
		except Exception:
			pass

	def _load_prefs(self):
		try:
			with open(self._prefs_path(), "r", encoding="utf-8") as f:
				prefs = json.load(f)
			self.dark_mode.set(bool(prefs.get("dark_mode", True)))
		except Exception:
			self.dark_mode.set(True)

	def _prefs_path(self):
		return os.path.join(os.path.abspath(os.path.dirname(__file__)), "settings.json")

	def _copy_result(self):
		text = self.result.get("1.0", tk.END).strip()
		if not text:
			return
		self.clipboard_clear()
		self.clipboard_append(text)
		if hasattr(self, "status"):
			self.status.configure(text="Скопировано в буфер обмена")

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

	def on_clear(self):
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

	def on_calculate(self):
		try:
			A = self._parse_matrix(self.textA.get("1.0", tk.END))
			B_or_b = self._parse_matrix(self.textB.get("1.0", tk.END))
		except Exception as e:
			messagebox.showerror("Ошибка ввода", str(e))
			return

		op = self.op_var.get()
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
				return

			if op == "transposeA":
				if A is None:
					raise ValueError("Нужно ввести A")
				self._set_result(self._format_matrix(A.T))
				if hasattr(self, "status"):
					self.status.configure(text="Выполнено: A^T")
				return
			if op == "transposeB":
				if B_or_b is None:
					raise ValueError("Нужно ввести B")
				self._set_result(self._format_matrix(B_or_b.T))
				if hasattr(self, "status"):
					self.status.configure(text="Выполнено: B^T")
				return

			if op == "detA":
				if A is None:
					raise ValueError("Нужно ввести A")
				val = float(np.linalg.det(A))
				self._set_result(f"det(A) = {val:g}")
				if hasattr(self, "status"):
					self.status.configure(text="Выполнено: det(A)")
				return
			if op == "detB":
				if B_or_b is None:
					raise ValueError("Нужно ввести B")
				val = float(np.linalg.det(B_or_b))
				self._set_result(f"det(B) = {val:g}")
				if hasattr(self, "status"):
					self.status.configure(text="Выполнено: det(B)")
				return

			if op == "rankA":
				if A is None:
					raise ValueError("Нужно ввести A")
				val = int(np.linalg.matrix_rank(A))
				self._set_result(f"rank(A) = {val}")
				if hasattr(self, "status"):
					self.status.configure(text="Выполнено: rank(A)")
				return
			if op == "rankB":
				if B_or_b is None:
					raise ValueError("Нужно ввести B")
				val = int(np.linalg.matrix_rank(B_or_b))
				self._set_result(f"rank(B) = {val}")
				if hasattr(self, "status"):
					self.status.configure(text="Выполнено: rank(B)")
				return

			if op == "invA":
				if A is None:
					raise ValueError("Нужно ввести A")
				res = np.linalg.inv(A)
				self._set_result(self._format_matrix(res))
				if hasattr(self, "status"):
					self.status.configure(text="Выполнено: A^{-1}")
				return
			if op == "invB":
				if B_or_b is None:
					raise ValueError("Нужно ввести B")
				res = np.linalg.inv(B_or_b)
				self._set_result(self._format_matrix(res))
				if hasattr(self, "status"):
					self.status.configure(text="Выполнено: B^{-1}")
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
				return

			raise ValueError("Неизвестная операция")
		except np.linalg.LinAlgError as e:
			self._set_result(f"Линейная алгебра: {str(e)}")
		except Exception as e:
			self._set_result(f"Ошибка: {str(e)}")

if __name__ == "__main__":
	app = MatrixApp()
	app.mainloop()
