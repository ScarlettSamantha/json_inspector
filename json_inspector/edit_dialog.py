from tkinter import ttk
import tkinter as tk
from typing import Any, Tuple


class EditValueDialog(tk.Toplevel):
    def __init__(self, master: tk.Tk, current_type: str, current_val: str) -> None:
        super().__init__(master)
        self.withdraw()
        self.transient(master)
        self.title("Edit Value")

        self.result: Tuple[str, Any] = (current_type, current_val)

        ttk.Label(self, text="Type:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.type_var = tk.StringVar(value=current_type)

        type_cb = ttk.Combobox(
            self,
            textvariable=self.type_var,
            values=["int", "float", "bool", "str", "NoneType"],
            state="readonly",
        )
        type_cb.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        type_cb.bind("<<ComboboxSelected>>", lambda e: self._render_value_field())

        self.value_frame = ttk.Frame(self)
        self.value_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5)

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="OK", command=self._on_ok).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="left")

        self._render_value_field(current_val)

        self.deiconify()
        self.wait_visibility()
        self.grab_set()
        self.focus_force()

    def _render_value_field(self, initial: str = "") -> None:
        for w in self.value_frame.winfo_children():
            w.destroy()

        t = self.type_var.get()
        ttk.Label(self.value_frame, text="Value:").grid(row=0, column=0, sticky="w")
        if t == "bool":
            self.val_var = tk.StringVar(value=str(initial))
            cb = ttk.Combobox(self.value_frame, textvariable=self.val_var, values=["True", "False"], state="readonly")
            cb.grid(row=0, column=1, sticky="ew")

        elif t == "NoneType":
            self.val_var = tk.StringVar(value="null")
            lbl = ttk.Label(self.value_frame, text="null")
            lbl.grid(row=0, column=1, sticky="w")
        else:
            self.val_var = tk.StringVar(value=initial)
            entry = ttk.Entry(self.value_frame, textvariable=self.val_var)
            entry.grid(row=0, column=1, sticky="ew")

            if t in ("int", "float"):

                def validate(s: str) -> bool:
                    if s == "":
                        return True
                    try:
                        int(s) if t == "int" else float(s)
                        return True
                    except ValueError:
                        return False

                vcmd = (self.register(lambda s: validate(s)), "%P")  #   type: ignore
                entry.configure(validate="key", validatecommand=vcmd)

        self.value_frame.columnconfigure(1, weight=1)

    def _on_ok(self) -> None:
        t = self.type_var.get()
        raw = self.val_var.get().strip().replace("'", "").replace('"', "")

        if t == "int":
            val = int(raw)
        elif t == "float":
            val = float(raw)
        elif t == "bool":
            val = raw == "True"
        elif t == "NoneType":
            val = None
        else:
            val = raw

        self.result = (t, val)
        self.destroy()
