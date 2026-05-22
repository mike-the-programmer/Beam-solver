import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')

class BeamApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Beam solver")
        self.grid_size = 40
        self.beam_y = 300
        self.active_tool = "Span"
        self.nodes, self.supports, self.point_loads, self.udl_loads = [], {}, [], []
        self.udl_start = None

        self.setup_ui()
        self.canvas.bind("<Configure>", lambda e: self.redraw())
        self.canvas.bind("<Button-1>", self.on_click)
        self.redraw()

    def setup_ui(self):
        panel = tk.Frame(self.root, width=240, bg="whitesmoke")
        panel.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(panel, text="STRUCTURAL TOOLS", font=("Arial", 12, "bold"), bg="white").pack(pady=10)
        self.tool_var = tk.StringVar(value="Span")

        for text, mode in [("Draw Span", "Span"), ("Place Support", "Support"), ("Add Point Load", "Point"), ("Add UDL", "UDL")]:
            ttk.Radiobutton(panel, text=text, value=mode, variable=self.tool_var, 
                            command=lambda: setattr(self, "active_tool", self.tool_var.get())).pack(fill="x", padx=15, pady=3)

        support_box = tk.LabelFrame(panel, text="Support Type", bg="white")
        support_box.pack(fill="x", padx=10, pady=10)
        self.supp_var = tk.StringVar(value="Pinned")
        for s in ["Pinned", "Roller", "Fixed"]:
            ttk.Radiobutton(support_box, text=s, value=s, variable=self.supp_var).pack(anchor="w")

        grid_box = tk.Frame(panel, bg="white")
        grid_box.pack(fill="x", padx=10, pady=10)
        tk.Label(grid_box, text="Grid:", bg="white").pack(side=tk.LEFT)
        self.grid_entry = ttk.Entry(grid_box, width=6)
        self.grid_entry.insert(0, "40")
        self.grid_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(grid_box, text="Set", command=self.set_grid).pack(side=tk.LEFT)

        ttk.Button(panel, text="Analyze", command=self.analyze).pack(fill="x", padx=10, pady=10)
        ttk.Button(panel, text="Clear", command=self.clear).pack(fill="x", padx=10)

        self.canvas = tk.Canvas(self.root, bg="white", cursor="cross")
        self.canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def set_grid(self):
        try:
            g = int(self.grid_entry.get())
            if g >= 20:
                self.grid_size = g
                self.redraw()
        except ValueError: pass

    def clear(self):
        self.nodes.clear(); self.supports.clear(); self.point_loads.clear(); self.udl_loads.clear()
        self.udl_start = None
        self.redraw()

    def snap(self, x): return round(x / self.grid_size)

    def redraw(self):
        self.canvas.delete("all")
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        minor = max(10, self.grid_size // 4)

        for x in range(0, w, minor): self.canvas.create_line(x, 0, x, h, fill="gainsboro")
        for y in range(0, h, minor): self.canvas.create_line(0, y, w, y, fill="gainsboro")
        for x in range(0, w, self.grid_size):
            self.canvas.create_line(x, 0, x, h, fill="darkgray")
            self.canvas.create_text(x, self.beam_y + 110, text=f"{x//self.grid_size}m", fill="gray", font=("Arial", 8))

        self.canvas.create_line(0, self.beam_y, w, self.beam_y, fill="lightgray")
        self.draw_elements()

    def draw_elements(self):
        if len(self.nodes) >= 2:
            for i in range(len(self.nodes) - 1):
                x1, x2 = self.nodes[i] * self.grid_size, self.nodes[i + 1] * self.grid_size
                self.canvas.create_line(x1, self.beam_y, x2, self.beam_y, fill="lightblue", width=6)
                self.canvas.create_text((x1 + x2) / 2, self.beam_y - 18, text=f"{self.nodes[i+1]-self.nodes[i]} m", font=("Arial", 9, "bold"))
        
        for i, t in self.supports.items():
            x = self.nodes[i] * self.grid_size
            if t == "Pinned": self.canvas.create_polygon(x, self.beam_y, x - 12, self.beam_y + 20, x + 12, self.beam_y + 20, fill="green")
            elif t == "Roller":
                self.canvas.create_polygon(x, self.beam_y, x - 12, self.beam_y + 16, x + 12, self.beam_y + 16, fill="royalblue")
                self.canvas.create_oval(x - 10, self.beam_y + 16, x + 10, self.beam_y + 22, fill="gray")
            else: self.canvas.create_rectangle(x - 8 if i == 0 else x, self.beam_y - 30, x if i == 0 else x + 8, self.beam_y + 30, fill="red")

        for p in self.point_loads:
            x = p["x"] * self.grid_size
            self.canvas.create_line(x, self.beam_y - 60, x, self.beam_y, arrow=tk.LAST, fill="darkorange", width=3)
            self.canvas.create_text(x, self.beam_y - 72, text=f"{p['P']} kN", fill="darkorange")

        for u in self.udl_loads:
            x1, x2 = u["x1"] * self.grid_size, u["x2"] * self.grid_size
            self.canvas.create_rectangle(x1, self.beam_y - 35, x2, self.beam_y, outline="purple", width=2, dash=(4, 2))
            self.canvas.create_text((x1 + x2) / 2, self.beam_y - 45, text=f"{u['w']} kN/m", fill="purple")

    def on_click(self, event):
        x = self.snap(event.x)
        if self.active_tool == "Span":
            if x not in self.nodes:
                self.nodes.append(x); self.nodes.sort()
                self.supports = {i: self.supports.get(i, "Pinned") for i in range(len(self.nodes))}
                self.redraw()
        elif self.active_tool == "Support" and x in self.nodes:
            self.supports[self.nodes.index(x)] = self.supp_var.get()
            self.redraw()
        elif self.active_tool == "Point" and self.nodes and self.nodes[0] <= x <= self.nodes[-1]:
            if p := simpledialog.askfloat("Point Load", "Load (kN):"):
                self.point_loads.append({"x": x, "P": p})
                self.redraw()
        elif self.active_tool == "UDL" and x in self.nodes:
            idx = self.nodes.index(x)
            if self.udl_start is None:
                self.udl_start = idx
                messagebox.showinfo("UDL", "Select ending node")
            else:
                x1, x2 = self.nodes[self.udl_start], self.nodes[idx]
                if w := simpledialog.askfloat("UDL", "Load (kN/m):"):
                    self.udl_loads.append({"x1": min(x1, x2), "x2": max(x1, x2), "w": w})
                self.udl_start = None
                self.redraw()

    def span_terms(self, i, L):
        s, e = self.nodes[i], self.nodes[i + 1]
        left = right = 0
        for p in self.point_loads:
            if s <= p["x"] <= e:
                a, b = p["x"] - s, e - p["x"]
                left += (p["P"] * a * b / L) * (L + a)
                right += (p["P"] * a * b / L) * (L + b)
        for u in self.udl_loads:
            if u["x1"] <= s and u["x2"] >= e:
                val = (u["w"] * L**3) / 4
                left += val; right += val
        return left, right

    def analyze(self):
        if len(self.nodes) < 2:
            return messagebox.showerror("Error", "Draw spans first")
        spans = [self.nodes[i + 1] - self.nodes[i] for i in range(len(self.nodes) - 1)]
        n = len(self.nodes)
        A, B = np.zeros((n, n)), np.zeros(n)

        for i in range(1, n - 1):
            L1, L2 = spans[i - 1], spans[i]
            A[i, i - 1], A[i, i], A[i, i + 1] = L1, 2 * (L1 + L2), L2
            _, r1 = self.span_terms(i - 1, L1)
            l2, _ = self.span_terms(i, L2)
            B[i] = -(r1 + l2)

        A[0, 0] = A[-1, -1] = 1
        try:
            self.plot(np.linalg.solve(A, B), spans)
        except np.linalg.LinAlgError:
            messagebox.showerror("Error", "Structure unstable")

    def plot(self, M, spans):
        X, V, BM, offset = [], [], [], 0
        for i, L in enumerate(spans):
               xs = np.linspace(0, L, 300)
               m1, m2 = M[i], M[i + 1]
               R = (m2 - m1) / L
               s, e = self.nodes[i], self.nodes[i + 1]

               for p in self.point_loads:
                   if s <= p["x"] <= e: R += p["P"] * (L - (p["x"] - s)) / L
               for u in self.udl_loads:
                   if u["x1"] <= s and u["x2"] >= e: R += (u["w"] * L) / 2

               Vx, Mx = np.ones_like(xs) * R, m1 + R * xs
               for p in self.point_loads:
                   if s <= p["x"] <= e:
                       a = p["x"] - s
                       Vx[xs >= a] -= p["P"]
                       Mx[xs >= a] -= p["P"] * (xs[xs >= a] - a)
               for u in self.udl_loads:
                   if u["x1"] <= s and u["x2"] >= e:
                       Vx -= u["w"] * xs
                       Mx -= u["w"] * xs**2 / 2

               X.extend(xs + offset); V.extend(Vx); BM.extend(Mx)
               offset += L

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
        for ax, data, title, col in [(ax1, V, "Shear Force Diagram", "green"), (ax2, BM, "Bending Moment Diagram", "blue")]:
               ax.plot(X, data, color=col, linewidth=2)
               ax.fill_between(X, 0, data, alpha=0.15, color=col)
               ax.axhline(0, color="black")
               ax.set_title(title)
               ax.grid(True, linestyle=":")
               for n in self.nodes: ax.axvline(n, linestyle="--", color="gray", alpha=0.5)

        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
       root = tk.Tk()
       app = BeamApp(root)
       root.mainloop()