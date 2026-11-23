"""
MedConnect — Interface Gestion des Patients (F002)
Auteur  : ALLABOUCH ANASS (Chef de Projet)
Version : 1.0

Interfaces couvertes (conformes au SFD MIL3_Dossier_Spec_Fonctionnelles_E12_V4) :
  Figure 2  — Liste des patients + recherche par CIN
  Figure 3  — Formulaire d'ajout d'un patient
  Figure 4  — Refus CIN déjà existant (message d'erreur inline)
  Figure 5  — Formulaire de modification d'un patient
  Figure 6  — Confirmation de suppression
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from patients.patient_service import PatientService

# ─── Palette couleurs (tons cabinet médical) ──────────────────────────────────
BG_MAIN    = "#F0F4F8"
BG_HEADER  = "#1E6FA5"
BG_TABLE   = "#FFFFFF"
BG_BTN_ADD = "#27AE60"
BG_BTN_MOD = "#2980B9"
BG_BTN_DEL = "#C0392B"
BG_BTN_SCH = "#8E44AD"
FG_WHITE   = "#FFFFFF"
FG_DARK    = "#2C3E50"
FG_GREY    = "#7F8C8D"
FONT_TITLE = ("Segoe UI", 15, "bold")
FONT_HEAD  = ("Segoe UI", 10, "bold")
FONT_BODY  = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 9)
FONT_ERR   = ("Segoe UI", 9, "italic")

COLUMNS = ("CIN", "Nom", "Prénom", "Date naiss.", "Téléphone",
           "Groupe sg.", "Allergies", "Contact urgence")

GROUPES = ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]


# ─────────────────────────────────────────────────────────────────────────────
class PatientApp(tk.Tk):
    """Fenêtre principale — F002 Gestion des Patients."""

    def __init__(self):
        super().__init__()
        self.title("MedConnect — Gestion des Patients (F002)")
        self.geometry("1100x680")
        self.minsize(900, 580)
        self.configure(bg=BG_MAIN)
        self.resizable(True, True)

        self.service = PatientService()
        self._preload_demo_data()

        self._build_header()
        self._build_toolbar()
        self._build_table()
        self._build_status_bar()

        self._refresh_table()

    # ── Données de démonstration ────────────────────────────────────────────
    def _preload_demo_data(self):
        samples = [
            ("AB123456", "Alami",    "Youssef",  "1990-05-15", "0601234567", "A+", "Pénicilline",  "0699111111"),
            ("CD789012", "Benali",   "Hassan",   "1985-03-20", "0612345678", "O-", "",              ""),
            ("EF345678", "Chaoui",   "Fatima",   "2000-11-01", "0623456789", "B+", "Aspirine",      "0677222222"),
        ]
        for args in samples:
            self.service.ajouter_patient(*args)

    # ── En-tête ─────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self, bg=BG_HEADER, height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr, text="🏥  MedConnect", bg=BG_HEADER, fg=FG_WHITE,
                 font=("Segoe UI", 16, "bold")).pack(side="left", padx=20, pady=10)

        tk.Label(hdr, text="F002 — Gestion des Patients", bg=BG_HEADER, fg="#D6EAF8",
                 font=("Segoe UI", 11)).pack(side="left", padx=5)

        tk.Label(hdr, text="Groupe 12 | FSA Agadir | 2026–2027",
                 bg=BG_HEADER, fg="#AED6F1", font=FONT_SMALL).pack(side="right", padx=20)

    # ── Barre d'outils ──────────────────────────────────────────────────────
    def _build_toolbar(self):
        bar = tk.Frame(self, bg=BG_MAIN, pady=8)
        bar.pack(fill="x", padx=16)

        # Recherche par CIN
        tk.Label(bar, text="Recherche par CIN :", bg=BG_MAIN,
                 fg=FG_DARK, font=FONT_HEAD).pack(side="left")

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(bar, textvariable=self.search_var,
                                     font=FONT_BODY, width=16, relief="solid", bd=1)
        self.search_entry.pack(side="left", padx=6)
        self.search_entry.bind("<Return>", lambda e: self._on_search())

        self._btn(bar, "🔍 Rechercher", BG_BTN_SCH, self._on_search).pack(side="left", padx=4)
        self._btn(bar, "✖ Effacer",    FG_GREY,    self._clear_search).pack(side="left")

        # Actions
        tk.Frame(bar, bg=BG_MAIN, width=30).pack(side="left")
        self._btn(bar, "➕ Ajouter",   BG_BTN_ADD, self._on_add).pack(side="left", padx=4)
        self._btn(bar, "✏ Modifier",   BG_BTN_MOD, self._on_edit).pack(side="left", padx=4)
        self._btn(bar, "🗑 Supprimer", BG_BTN_DEL, self._on_delete).pack(side="left", padx=4)

        # Compteur
        self.lbl_count = tk.Label(bar, text="", bg=BG_MAIN, fg=FG_GREY, font=FONT_SMALL)
        self.lbl_count.pack(side="right", padx=10)

    # ── Tableau ──────────────────────────────────────────────────────────────
    def _build_table(self):
        frame = tk.Frame(self, bg=BG_MAIN)
        frame.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background=BG_TABLE, foreground=FG_DARK,
                        rowheight=28, fieldbackground=BG_TABLE,
                        font=FONT_BODY)
        style.configure("Treeview.Heading",
                        background=BG_HEADER, foreground=FG_WHITE,
                        font=FONT_HEAD, relief="flat")
        style.map("Treeview",
                  background=[("selected", "#D6EAF8")],
                  foreground=[("selected", FG_DARK)])

        self.tree = ttk.Treeview(frame, columns=COLUMNS, show="headings",
                                  selectmode="browse")

        col_widths = [90, 110, 110, 100, 110, 80, 130, 120]
        for col, w in zip(COLUMNS, col_widths):
            self.tree.heading(col, text=col, anchor="w")
            self.tree.column(col, width=w, anchor="w", minwidth=60)

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        # Alternance couleurs de lignes
        self.tree.tag_configure("even", background="#EBF5FB")
        self.tree.tag_configure("odd",  background=BG_TABLE)

        self.tree.bind("<Double-1>", lambda e: self._on_edit())

    # ── Barre de statut ──────────────────────────────────────────────────────
    def _build_status_bar(self):
        self.status_var = tk.StringVar(value="Prêt.")
        bar = tk.Frame(self, bg="#D5DBDB", height=24)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        tk.Label(bar, textvariable=self.status_var, bg="#D5DBDB",
                 fg=FG_DARK, font=FONT_SMALL, anchor="w").pack(side="left", padx=10)

    # ── Utilitaire bouton ─────────────────────────────────────────────────────
    @staticmethod
    def _btn(parent, text, color, cmd):
        return tk.Button(parent, text=text, bg=color, fg=FG_WHITE,
                         font=FONT_HEAD, relief="flat", cursor="hand2",
                         padx=10, pady=4, command=cmd,
                         activebackground=color, activeforeground=FG_WHITE)

    # ── Rafraîchir le tableau ─────────────────────────────────────────────────
    def _refresh_table(self, patients=None):
        for row in self.tree.get_children():
            self.tree.delete(row)
        lst = patients if patients is not None else self.service.lister_patients()
        for i, p in enumerate(lst):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert("", "end", iid=p.cin, tags=(tag,),
                             values=(p.cin, p.nom, p.prenom, p.date_naissance,
                                     p.telephone, p.groupe_sanguin,
                                     p.allergies, p.contact_urgence))
        total = self.service.nombre_patients()
        shown = len(lst) if patients is not None else total
        self.lbl_count.config(text=f"{shown} patient(s) affichés / {total} total")

    # ── Recherche ─────────────────────────────────────────────────────────────
    def _on_search(self):
        cin = self.search_var.get().strip()
        if not cin:
            self._refresh_table()
            self.status_var.set("Affichage de tous les patients.")
            return
        try:
            p = self.service.rechercher_patient(cin)
            self._refresh_table([p])
            self.tree.selection_set(p.cin)
            self.status_var.set(f"Patient trouvé : {p.prenom} {p.nom} (CIN {p.cin})")
        except ValueError as e:
            # Figure 4 — message erreur inline dans status bar
            messagebox.showerror(
                "Patient introuvable",
                f"Aucun patient trouvé avec le CIN « {cin} ».\n\n"
                f"Vérifiez l'identifiant et réessayez.",
                parent=self
            )
            self.status_var.set(f"⚠ Erreur : {e}")

    def _clear_search(self):
        self.search_var.set("")
        self._refresh_table()
        self.status_var.set("Recherche effacée — tous les patients affichés.")

    # ── Ajout ─────────────────────────────────────────────────────────────────
    def _on_add(self):
        """Ouvre Figure 3 — Formulaire d'ajout."""
        PatientForm(self, title="Ajouter un patient", on_save=self._save_new)

    def _save_new(self, data):
        try:
            self.service.ajouter_patient(**data)
            self._refresh_table()
            self.status_var.set(
                f"✅ Patient {data['prenom']} {data['nom']} (CIN {data['cin']}) ajouté avec succès.")
        except ValueError as e:
            # Figure 4 — refus CIN/téléphone doublon
            messagebox.showerror("Ajout refusé", str(e), parent=self)
            self.status_var.set(f"⚠ Ajout refusé : {e}")

    # ── Modification ──────────────────────────────────────────────────────────
    def _on_edit(self):
        """Ouvre Figure 5 — Formulaire de modification."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Sélection requise",
                                "Veuillez sélectionner un patient dans la liste.",
                                parent=self)
            return
        cin = sel[0]
        try:
            patient = self.service.rechercher_patient(cin)
        except ValueError as e:
            messagebox.showerror("Erreur", str(e), parent=self)
            return

        initial = {
            "cin": patient.cin,
            "nom": patient.nom,
            "prenom": patient.prenom,
            "date_naissance": patient.date_naissance,
            "telephone": patient.telephone,
            "groupe_sanguin": patient.groupe_sanguin,
            "allergies": patient.allergies,
            "contact_urgence": patient.contact_urgence,
        }
        PatientForm(self, title="Modifier le patient", initial=initial,
                    edit_mode=True, on_save=self._save_edit)

    def _save_edit(self, data):
        cin = data.pop("cin")
        try:
            self.service.modifier_patient(cin, **data)
            self._refresh_table()
            self.status_var.set(f"✅ Patient CIN {cin} modifié avec succès.")
        except ValueError as e:
            messagebox.showerror("Modification refusée", str(e), parent=self)
            self.status_var.set(f"⚠ Modification refusée : {e}")

    # ── Suppression ───────────────────────────────────────────────────────────
    def _on_delete(self):
        """Figure 6 — Confirmation de suppression."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Sélection requise",
                                "Veuillez sélectionner un patient à supprimer.",
                                parent=self)
            return
        cin = sel[0]
        try:
            patient = self.service.rechercher_patient(cin)
        except ValueError as e:
            messagebox.showerror("Erreur", str(e), parent=self)
            return

        # Figure 6 — dialogue de confirmation
        confirm = messagebox.askyesno(
            "Confirmation de suppression",
            f"Êtes-vous sûr de vouloir supprimer le patient ?\n\n"
            f"  CIN     : {patient.cin}\n"
            f"  Nom     : {patient.prenom} {patient.nom}\n"
            f"  Tél.    : {patient.telephone}\n\n"
            f"⚠  Cette action est irréversible.",
            icon="warning",
            parent=self
        )
        if not confirm:
            self.status_var.set("Suppression annulée.")
            return

        try:
            self.service.supprimer_patient(cin)
            self._refresh_table()
            self.status_var.set(
                f"🗑 Patient {patient.prenom} {patient.nom} (CIN {cin}) supprimé.")
        except ValueError as e:
            messagebox.showerror("Erreur suppression", str(e), parent=self)


# ─────────────────────────────────────────────────────────────────────────────
class PatientForm(tk.Toplevel):
    """
    Figure 3 — Formulaire d'ajout   / Figure 5 — Formulaire de modification.
    Réutilise la même fenêtre modale avec un paramètre `edit_mode`.
    """

    FIELDS = [
        ("cin",             "CIN *",                  False, None),
        ("nom",             "Nom *",                  False, None),
        ("prenom",          "Prénom *",               False, None),
        ("date_naissance",  "Date de naissance *",    False, None),
        ("telephone",       "Téléphone *",            False, None),
        ("groupe_sanguin",  "Groupe sanguin",         True,  GROUPES),
        ("allergies",       "Allergies",              False, None),
        ("contact_urgence", "Contact d'urgence",      False, None),
    ]

    def __init__(self, parent, title, on_save, initial=None, edit_mode=False):
        super().__init__(parent)
        self.title(title)
        self.on_save = on_save
        self.edit_mode = edit_mode
        self.initial = initial or {}

        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        self.configure(bg=BG_MAIN)

        self._build_form()
        self._populate(self.initial)

        # Centrer sur parent
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        py = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")
        self.focus_set()

    def _build_form(self):
        # En-tête coloré
        hdr = tk.Frame(self, bg=BG_HEADER, height=44)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ico = "✏" if self.edit_mode else "➕"
        tk.Label(hdr, text=f"{ico}  {self.title()}",
                 bg=BG_HEADER, fg=FG_WHITE, font=FONT_TITLE).pack(side="left", padx=16, pady=8)

        # Corps formulaire
        body = tk.Frame(self, bg=BG_MAIN, padx=24, pady=16)
        body.pack(fill="both")

        self.entries = {}
        self.error_labels = {}

        for key, label, is_combo, choices in self.FIELDS:
            row = tk.Frame(body, bg=BG_MAIN)
            row.pack(fill="x", pady=4)

            lbl = tk.Label(row, text=label, bg=BG_MAIN, fg=FG_DARK,
                           font=FONT_HEAD, width=22, anchor="w")
            lbl.pack(side="left")

            if is_combo:
                var = tk.StringVar()
                widget = ttk.Combobox(row, textvariable=var, values=choices,
                                      state="readonly", width=22, font=FONT_BODY)
                widget.pack(side="left")
                self.entries[key] = var
            else:
                var = tk.StringVar()
                widget = tk.Entry(row, textvariable=var, font=FONT_BODY,
                                  width=25, relief="solid", bd=1,
                                  state="disabled" if (self.edit_mode and key == "cin") else "normal")
                widget.pack(side="left")
                self.entries[key] = var

            # Label d'erreur inline (rouge, discret)
            err = tk.Label(row, text="", bg=BG_MAIN, fg="#E74C3C", font=FONT_ERR)
            err.pack(side="left", padx=6)
            self.error_labels[key] = err

        # Note champs obligatoires
        tk.Label(body, text="* Champ obligatoire", bg=BG_MAIN,
                 fg=FG_GREY, font=FONT_SMALL).pack(anchor="w", pady=(4, 0))

        # Boutons
        btn_frame = tk.Frame(self, bg=BG_MAIN, pady=12)
        btn_frame.pack()

        color = BG_BTN_MOD if self.edit_mode else BG_BTN_ADD
        label = "💾 Enregistrer" if self.edit_mode else "✅ Ajouter le patient"
        tk.Button(btn_frame, text=label, bg=color, fg=FG_WHITE,
                  font=FONT_HEAD, relief="flat", padx=14, pady=6,
                  cursor="hand2", command=self._on_submit).pack(side="left", padx=8)

        tk.Button(btn_frame, text="✖ Annuler", bg=FG_GREY, fg=FG_WHITE,
                  font=FONT_HEAD, relief="flat", padx=14, pady=6,
                  cursor="hand2", command=self.destroy).pack(side="left", padx=8)

    def _populate(self, data):
        for key, var in self.entries.items():
            var.set(data.get(key, ""))

    def _on_submit(self):
        # Effacer anciennes erreurs
        for lbl in self.error_labels.values():
            lbl.config(text="")

        data = {key: var.get().strip() for key, var in self.entries.items()}

        # Validation locale (affichage inline)
        required = [("cin", "CIN"), ("nom", "Nom"), ("prenom", "Prénom"),
                    ("date_naissance", "Date de naissance"), ("telephone", "Téléphone")]
        ok = True
        for key, label in required:
            if not data[key]:
                self.error_labels[key].config(text=f"⚠ {label} obligatoire")
                ok = False

        if not ok:
            return

        self.on_save(data)
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
def run():
    app = PatientApp()
    app.mainloop()


if __name__ == "__main__":
    run()
