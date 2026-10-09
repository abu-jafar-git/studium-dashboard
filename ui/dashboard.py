import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from backend.controller import DashboardController
from backend.models.constants import (
    HINTERGRUND_FARBE, KARTE_HINTERGRUND, TEXT_DUNKEL, TEXT_HELL, RAHMEN_FARBE,
    FARBE_BESTANDEN, FARBE_AKTIV, FARBE_BLAU, FARBE_VIOLETT, FARBE_INDIGO,
    SCHRIFT_TITEL, SCHRIFT_H2, SCHRIFT_KPI_WERT, SCHRIFT_KPI_LABEL, SCHRIFT_NORMAL, SCHRIFT_KLEIN,
    STATUS_FARBEN, STATUS_GEPLANT, STATUS_BESTANDEN, STATUS_NICHT_BESTANDEN,
    ALLE_MODUL_STATUS, MOEGLICHE_PRUEFUNGSARTEN, MOEGLICHE_VERSUCHE, WP_BEREICHE
)
from backend.models.modul import Modul, WahlpflichtModul

class ScrollableFrame(tk.Frame):
    """
    Eine wiederverwendbare Komponente für scrollbaren Inhalt.
    """
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)

        # Canvas und Scrollbar erstellen
        self.canvas = tk.Canvas(self, bg=kwargs.get("bg", HINTERGRUND_FARBE), highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)

        # Der innere Frame, der den eigentlichen Inhalt hält
        self.scrollable_frame = tk.Frame(self.canvas, bg=kwargs.get("bg", HINTERGRUND_FARBE))

        # Konfiguration: Wenn der innere Frame wächst, passe die Scrollregion an
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # Fenster im Canvas erstellen
        self.window_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Scrollbar mit Canvas verbinden
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Layout
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Mausrad nur aktiv, solange die Maus über diesem Bereich ist
        self.bind("<Enter>", self._mausrad_aktivieren)
        self.bind("<Leave>", self._mausrad_deaktivieren)

        # Breite anpassen
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.window_id, width=event.width)

    def _mausrad_aktivieren(self, event=None):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _mausrad_deaktivieren(self, event):
        # Maus nur dann "raus", wenn sie auch kein Kind-Widget in diesem Bereich berührt
        try:
            widget = self.winfo_containing(event.x_root, event.y_root)
        except KeyError:
            widget = None
        while widget is not None:
            if widget is self:
                return
            widget = widget.master
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        # Nur scrollen, wenn das Canvas sichtbar ist
        if self.canvas.winfo_exists():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class StudienDashboard:
    """
    Die Haupt-GUI-Klasse der Anwendung.
    Sie ist verantwortlich für das Zeichnen des Dashboards.
    Die Logik und DB-Kommunikation erfolgt über den DashboardController.
    """

    def __init__(self, root: tk.Tk, controller: DashboardController):
        """
        Initialisiert das Dashboard.

        :param root: Das tkinter-Hauptfenster.
        :param controller: Der Controller, der die Logik steuert.
        """
        self.root = root
        self.controller = controller

        # View beim Controller registrieren
        self.controller.set_view(self)

        self.studiengang = None

        # Konfiguriert das Hauptfenster
        self.root.title("Studien-Dashboard")
        self.root.geometry("1200x800")
        self.root.configure(bg=HINTERGRUND_FARBE)

        self._initialisiere_styles()
        self.lade_und_zeichne_dashboard()

    #Öffentliche Methoden für den Controller

    def zeige_erfolgsmeldung(self, nachricht: str):
        """Zeigt eine standardisierte Erfolgsmeldung an."""
        messagebox.showinfo("Erfolg", nachricht)

    def zeige_fehlermeldung(self, nachricht: str):
        """Zeigt eine standardisierte Fehlermeldung an."""
        messagebox.showerror("Fehler", nachricht)

    # Rendering-Methoden

    def _initialisiere_styles(self):
        """
        Definiert einmalig alle ttk-Styles für die Anwendung.
        """
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background=HINTERGRUND_FARBE)
        style.configure("Card.TFrame", background=KARTE_HINTERGRUND)
        style.configure("TLabel", background=HINTERGRUND_FARBE, foreground=TEXT_DUNKEL, font=SCHRIFT_NORMAL)
        style.configure("Blue.Horizontal.TProgressbar", troughcolor=RAHMEN_FARBE, background=FARBE_BLAU, thickness=8)
        style.configure("Green.Horizontal.TProgressbar", troughcolor=RAHMEN_FARBE, background=FARBE_BESTANDEN, thickness=8)
        style.configure("Violet.Horizontal.TProgressbar", troughcolor=RAHMEN_FARBE, background=FARBE_VIOLETT, thickness=8)

    def lade_und_zeichne_dashboard(self):
        """
        Die zentrale "Refresh"-Methode für die Hauptansicht.
        Lädt alle Daten neu und zeichnet das gesamte Dashboard.
        """
        # 1. Daten über den Controller laden.
        self.studiengang = self.controller.lade_studiengang()

        # 2. Alte UI-Elemente entfernen, um die Ansicht zu erneuern.
        for widget in self.root.winfo_children():
            widget.destroy()

        # Haupt-Container für den gesamten Inhalt
        main_frame = tk.Frame(self.root, bg=HINTERGRUND_FARBE, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        # 3. Die einzelnen UI-Sektionen werden der Reihe nach gezeichnet.
        self._zeichne_header(main_frame)
        self._zeichne_kpi_karten(main_frame)
        self._zeichne_semester_uebersicht(main_frame)

    def _zeichne_header(self, parent: tk.Frame):
        """
        Zeichnet den Titel und die globalen Aktions-Buttons.
        """
        header_frame = tk.Frame(parent, bg=HINTERGRUND_FARBE)
        header_frame.pack(fill="x", pady=(0, 20))

        # Der Titel kann sich jetzt immer auf self.studiengang.name verlassen.
        tk.Label(header_frame, text=self.studiengang.name, font=SCHRIFT_TITEL,
                 bg=HINTERGRUND_FARBE, fg=TEXT_DUNKEL).pack(side="left")

        # Button-Container auf der rechten Seite
        btn_container = tk.Frame(header_frame, bg=HINTERGRUND_FARBE)
        btn_container.pack(side="right")

        # Buttons mit angepasstem Design und Reihenfolge
        tk.Button(btn_container, text="🗑 DB Leeren", bg="#ef4444", fg="white", font=SCHRIFT_KLEIN, padx=10,
                  command=self.oeffne_db_leeren_dialog).pack(side="left", padx=5)

        tk.Button(btn_container, text="📥 Testdaten laden", bg=FARBE_INDIGO, fg="white", font=SCHRIFT_KLEIN, padx=10,
                  command=self.oeffne_testdaten_dialog).pack(side="left", padx=5)

        tk.Button(btn_container, text="Modul-Verwaltung", bg=TEXT_DUNKEL, fg="white", font=SCHRIFT_KLEIN, padx=10,
                  command=self.oeffne_modul_verwaltung).pack(side="left", padx=5)

        tk.Button(btn_container, text="⚙ Einstellungen", bg="white", fg=TEXT_HELL, font=SCHRIFT_KLEIN, padx=10,
                  command=self.oeffne_einstellungen).pack(side="left", padx=5)

        tk.Button(btn_container, text="💾 Backup (CSV)", bg="white", fg=TEXT_DUNKEL, font=SCHRIFT_KLEIN, padx=10,
                  command=self.exportiere_csv).pack(side="left")

    def _zeichne_kpi_karten(self, parent: tk.Frame):
        """
        Zeichnet die vier KPI-Karten. Kann sich darauf verlassen, dass self.studiengang existiert.
        """
        kpi_frame = tk.Frame(parent, bg=HINTERGRUND_FARBE)
        kpi_frame.pack(fill="x", pady=(0, 20))
        for i in range(4):
            kpi_frame.grid_columnconfigure(i, weight=1)

        schnitt = self.studiengang.aktuelle_notenschnitt
        erreichte_ects = self.studiengang.aktuelle_ects
        ziel_ects = self.studiengang.ziel_ects
        abgeschlossene_module = self.studiengang.abgeschlossene_module
        gesamte_module = self.studiengang.gesamte_module
        vergangene_monate = self.studiengang.aktuelle_zeit_in_monat
        ziel_dauer = self.studiengang.ziel_abschlussdauer

        self._zeichne_eine_kpi_karte(kpi_frame, 0, "NOTENSCHNITT", f"{schnitt:.2f}" if schnitt > 0 else "N/A",
                                     f"Ziel: {self.studiengang.ziel_notenschnitt or '-'}", FARBE_AKTIV)

        self._zeichne_eine_kpi_karte(kpi_frame, 1, "ECTS FORTSCHRITT", str(erreichte_ects),
                                     f"von {ziel_ects}" if ziel_ects is not None else "von -", FARBE_BLAU,
                                     fortschritt=erreichte_ects, maximum=ziel_ects, stil="Blue")

        self._zeichne_eine_kpi_karte(kpi_frame, 2, "ZEITVERLAUF (MONATE)", str(vergangene_monate),
                                     f"von {ziel_dauer}" if ziel_dauer is not None else "von -", FARBE_BESTANDEN,
                                     fortschritt=vergangene_monate, maximum=ziel_dauer, stil="Green")

        self._zeichne_eine_kpi_karte(kpi_frame, 3, "MODULE ABGESCHLOSSEN", str(abgeschlossene_module), f"von {gesamte_module}", FARBE_VIOLETT,
                                     fortschritt=abgeschlossene_module, maximum=gesamte_module, stil="Violet")

    def _zeichne_eine_kpi_karte(self, parent, spalte, titel, wert, subtext, farbe, fortschritt=None, maximum=None, stil=None):
        """Hilfsmethode zum Zeichnen einer einzelnen KPI-Karte."""
        frame = tk.Frame(parent, bg=KARTE_HINTERGRUND, highlightbackground=RAHMEN_FARBE, highlightthickness=1)
        frame.grid(row=0, column=spalte, padx=10, sticky="nsew")
        tk.Frame(frame, bg=farbe, width=4).pack(side="left", fill="y")
        inhalt = tk.Frame(frame, bg=KARTE_HINTERGRUND, padx=15, pady=15)
        inhalt.pack(side="left", fill="both", expand=True)
        tk.Label(inhalt, text=titel, font=SCHRIFT_KPI_LABEL, fg=TEXT_HELL, bg=KARTE_HINTERGRUND).pack(anchor="w")
        wert_frame = tk.Frame(inhalt, bg=KARTE_HINTERGRUND)
        wert_frame.pack(anchor="w", pady=(5, 0))
        tk.Label(wert_frame, text=wert, font=SCHRIFT_KPI_WERT, fg=TEXT_DUNKEL, bg=KARTE_HINTERGRUND).pack(side="left")
        tk.Label(wert_frame, text=subtext, font=SCHRIFT_KLEIN, fg=TEXT_HELL, bg=KARTE_HINTERGRUND).pack(side="left", padx=(5, 0))
        if fortschritt is not None and stil:
            pb = ttk.Progressbar(inhalt, style=f"{stil}.Horizontal.TProgressbar", length=100, value=fortschritt, maximum=maximum)
            pb.pack(fill="x", pady=(10, 0))

    def _zeichne_semester_uebersicht(self, parent: tk.Frame):
        """
        Zeichnet den Container für die Semester und füllt ihn.
        """
        nav_frame = tk.Frame(parent, bg=HINTERGRUND_FARBE)
        nav_frame.pack(fill="x", pady=(20, 10))
        tk.Label(nav_frame, text="Semesterübersicht", font=SCHRIFT_H2, bg=HINTERGRUND_FARBE, fg=TEXT_DUNKEL).pack(side="left")

        tk.Button(nav_frame, text="- Sem.", command=self._remove_semester).pack(side="right", padx=5)
        tk.Button(nav_frame, text="+ Sem.", command=self._add_semester).pack(side="right")

        # Container für die Semester-Kacheln
        raster_container = tk.Frame(parent, bg=KARTE_HINTERGRUND, padx=20, pady=20)
        raster_container.pack(fill="both", expand=True)
        for i in range(6):
            raster_container.grid_columnconfigure(i, weight=1)

        # Wenn die Liste der Semester leer ist, zeige eine Meldung.
        if not self.studiengang.semester_liste:
            tk.Label(raster_container, text="Keine Semester vorhanden. Bitte fügen Sie welche hinzu.",
                     font=SCHRIFT_H2, bg=KARTE_HINTERGRUND, fg=TEXT_HELL).pack(pady=20)
            return

        # Zeichne die Semester-Kacheln.
        for i, semester in enumerate(self.studiengang.semester_liste):
            self._zeichne_semester_kachel(raster_container, i, semester)

    def _zeichne_semester_kachel(self, eltern, index, semester):
        """Erstellt eine Kachel für ein Semester im alten Design."""
        status_text = "Aktiv" if semester.ist_aktiv else "Nicht aktiv"

        if semester.ist_aktiv:
            bg = FARBE_BLAU
            fg = "white"
            status_fg = "white"
            cursor = "hand2"
        else:
            bg = KARTE_HINTERGRUND
            fg = TEXT_DUNKEL
            status_fg = TEXT_HELL
            cursor = "hand2"

        row_idx = index // 6
        col_idx = index % 6

        f = tk.Frame(eltern, bg=bg, highlightbackground=RAHMEN_FARBE if not semester.ist_aktiv else bg,
                     highlightthickness=1, cursor=cursor)
        f.grid(row=row_idx, column=col_idx, padx=5, pady=5, sticky="ewns")

        inner = tk.Frame(f, bg=bg, padx=10, pady=20)
        inner.pack(fill="both", expand=True)

        l1 = tk.Label(inner, text=f"Sem. {semester.nummer}", font=("Helvetica", 12, "bold"), bg=bg, fg=fg)
        l1.pack()

        l2 = tk.Label(inner, text=status_text, font=("Helvetica", 8, "bold"), bg=bg, fg=status_fg)
        l2.pack(pady=(5, 0))

        # Binden des Klick-Events
        for w in [f, inner, l1, l2]:
            w.bind("<Button-1>", lambda e, s_id=semester.id: self.zeige_semester_detail(s_id))

    def _zeichne_modul_karte(self, parent, row, col, modul: Modul):
        """Zeichnet eine einzelne Modul-Karte im alten Design."""
        farbe = STATUS_FARBEN.get(modul.status, RAHMEN_FARBE)

        frame = tk.Frame(parent, bg=KARTE_HINTERGRUND, highlightbackground=farbe,
                         highlightthickness=2 if modul.status != STATUS_GEPLANT else 1,
                         width=320, height=240)
        frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        frame.pack_propagate(False)

        inner = tk.Frame(frame, bg=KARTE_HINTERGRUND, padx=15, pady=12)
        inner.pack(fill="both", expand=True)

        # --- OBEN: Status & Kennung ---
        header = tk.Frame(inner, bg=KARTE_HINTERGRUND, height=25)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text=modul.status.upper(), font=("Helvetica", 7, "bold"),
                 fg=farbe if modul.status != STATUS_GEPLANT else TEXT_HELL, bg=KARTE_HINTERGRUND).pack(side="left")

        if isinstance(modul, WahlpflichtModul):
            tk.Label(header, text=f"WP {modul.wahlpflichtbereich}", font=("Helvetica", 7, "bold"),
                     fg=TEXT_HELL, bg="#f1f5f9", padx=4).pack(side="right")

        if modul.code:
            tk.Label(header, text=modul.code, font=("Helvetica", 7),
                     fg=TEXT_HELL, bg=KARTE_HINTERGRUND).pack(side="right", padx=5)

        # --- MITTE: Name & Prüfung ---
        title_area = tk.Frame(inner, bg=KARTE_HINTERGRUND, height=60)
        title_area.pack(fill="x", pady=5)
        title_area.pack_propagate(False)

        tk.Label(title_area, text=modul.name, font=("Helvetica", 10, "bold"), fg=TEXT_DUNKEL,
                 bg=KARTE_HINTERGRUND, wraplength=260, justify="left").pack(anchor="w")

        art = modul.hole_pruefungsart() or "Klausur"
        tk.Label(inner, text=art, font=("Helvetica", 8), fg=TEXT_HELL, bg=KARTE_HINTERGRUND).pack(anchor="w")

        # --- UNTEN: Werte (ECTS/Note) ---
        footer = tk.Frame(inner, bg=KARTE_HINTERGRUND)
        footer.pack(fill="x", pady=(5, 5))

        ects_f = tk.Frame(footer, bg=KARTE_HINTERGRUND)
        ects_f.pack(side="left")
        tk.Label(ects_f, text="ECTS", font=("Helvetica", 7, "bold"), fg=TEXT_HELL, bg=KARTE_HINTERGRUND).pack(
            anchor="w")
        tk.Label(ects_f, text=str(modul.ects), font=("Helvetica", 9, "bold"), bg=KARTE_HINTERGRUND).pack(anchor="w")

        note_f = tk.Frame(footer, bg=KARTE_HINTERGRUND)
        note_f.pack(side="right")

        note_val = modul.hole_note()
        note_text = str(note_val) if note_val is not None else "--"

        tk.Label(note_f, text="NOTE", font=("Helvetica", 7, "bold"), fg=TEXT_HELL, bg=KARTE_HINTERGRUND).pack(
            anchor="e")
        tk.Label(note_f, text=note_text, font=("Helvetica", 14, "bold"), fg=TEXT_DUNKEL, bg=KARTE_HINTERGRUND).pack(
            anchor="e")

        # --- GANZ UNTEN: Die Button-Leiste ---
        btn_container = tk.Frame(inner, bg=KARTE_HINTERGRUND)
        btn_container.pack(side="bottom", fill="x", pady=(5, 0))

        tk.Frame(btn_container, bg=RAHMEN_FARBE, height=1).pack(fill="x", pady=5)
        btn_bar = tk.Frame(btn_container, bg=KARTE_HINTERGRUND)
        btn_bar.pack(fill="x")

        # Bearbeiten
        tk.Button(btn_bar, text="✎ Bearbeiten", font=("Helvetica", 8), bg="#f1f5f9", fg=FARBE_BLAU,
                  relief="flat", command=lambda: self.oeffne_modul_editor(modul)).pack(side="left", expand=True,
                                                                                       fill="x", padx=1)

        # Raus (nur wenn im Semester)
        if modul.semester_id:
            tk.Button(btn_bar, text="✕ Raus", font=("Helvetica", 8), bg="#fff7ed", fg="#ea580c",
                      relief="flat",
                      command=lambda m=modul: self.entferne_modul_aus_semester_click(m)).pack(side="left", expand=True,
                                                                                              fill="x", padx=1)
        else:
            tk.Frame(btn_bar, bg=KARTE_HINTERGRUND).pack(side="left", expand=True, fill="x")

        # Löschen
        tk.Button(btn_bar, text="🗑 Löschen", font=("Helvetica", 8), bg="#fee2e2", fg="#ef4444",
                  relief="flat", command=lambda m=modul: self.loesche_modul_click(m)).pack(side="left", expand=True,
                                                                                           fill="x", padx=1)



    #Navigation

    def zeige_semester_detail(self, semester_id):
        """
        Zeigt die Detailansicht eines Semesters mit allen Modulen.
        """
        # 1. Semester-Objekt laden (inkl. Module)
        semester = self.controller.lade_semester(semester_id)
        if not semester:
            return

        # 3. UI leeren
        for widget in self.root.winfo_children():
            widget.destroy()

        main_frame = tk.Frame(self.root, bg=HINTERGRUND_FARBE, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        # --- Header ---
        header_frame = tk.Frame(main_frame, bg=HINTERGRUND_FARBE)
        header_frame.pack(fill="x", pady=(0, 20))

        tk.Button(header_frame, text="← Zurück", command=self.lade_und_zeichne_dashboard,
                  bg="white", fg=TEXT_DUNKEL, relief="flat", padx=10, pady=5).pack(side="left", padx=(0, 20))

        tk.Label(header_frame, text=f"Semester {semester.nummer}", font=SCHRIFT_TITEL,
                 bg=HINTERGRUND_FARBE, fg=TEXT_DUNKEL).pack(side="left")

        tk.Button(header_frame, text="+ Modul hinzufügen",
                  command=lambda: self.oeffne_modul_hinzufuegen_dialog(semester_id),
                  bg=FARBE_BLAU, fg="white", font=SCHRIFT_KLEIN, padx=10).pack(side="right")

        if not semester.ist_aktiv:
            tk.Button(header_frame, text="✓ Als aktiv setzen",
                      command=lambda: self.controller.setze_aktives_semester(semester_id),
                      bg=FARBE_BESTANDEN, fg="white", font=SCHRIFT_KLEIN, padx=10).pack(side="right", padx=(0, 10))

        # --- Scrollbarer Bereich für Module ---
        scroll_area = ScrollableFrame(main_frame, bg=HINTERGRUND_FARBE)
        scroll_area.pack(fill="both", expand=True)

        # --- Module Grid ---
        mod_frame = tk.Frame(scroll_area.scrollable_frame, bg=HINTERGRUND_FARBE)
        mod_frame.pack(fill="both", expand=True)

        # Grid-Konfiguration (3 Spalten)
        for i in range(3):
            mod_frame.grid_columnconfigure(i, weight=1)

        row = 0
        col = 0
        for modul in semester.module:
            self._zeichne_modul_karte(mod_frame, row, col, modul)
            col += 1
            if col > 2:
                col = 0
                row += 1

        legende_frame = tk.Frame(scroll_area.scrollable_frame, bg=HINTERGRUND_FARBE)
        legende_frame.pack(fill="x", pady=30)

        tk.Label(legende_frame, text="MODUL-STATUS LEGENDE", font=("Helvetica", 9, "bold"), fg=TEXT_HELL,
                 bg=HINTERGRUND_FARBE).pack(anchor="center", pady=(10, 5))

        l_container = tk.Frame(legende_frame, bg=HINTERGRUND_FARBE)
        l_container.pack(anchor="center")

        for text, farbe_kreis in STATUS_FARBEN.items():
            f = tk.Frame(l_container, bg=HINTERGRUND_FARBE)
            f.pack(side="left", padx=10)
            c = tk.Canvas(f, width=12, height=12, bg=HINTERGRUND_FARBE, highlightthickness=0)
            c.create_oval(0, 0, 12, 12, fill=farbe_kreis, outline="")
            c.pack(side="left", padx=(0, 5))
            tk.Label(f, text=text, font=SCHRIFT_KLEIN, fg=TEXT_DUNKEL, bg=HINTERGRUND_FARBE).pack(side="left")

        # --- KPI Container (Semester-Statistiken) ---
        kpi_frame = tk.Frame(scroll_area.scrollable_frame, bg=HINTERGRUND_FARBE)
        kpi_frame.pack(fill="x", pady=(20, 0), before=mod_frame) # Vor den Modulen anzeigen
        kpi_frame.grid_columnconfigure(0, weight=1)
        kpi_frame.grid_columnconfigure(1, weight=1)

        # Notenschnitt (aus DB)
        schnitt = semester.notenschnitt_semester
        wert_schnitt = f"{schnitt:.2f}" if schnitt and schnitt > 0 else "-"
        self._zeichne_eine_kpi_karte(kpi_frame, 0, "SCHNITT SEMESTER", wert_schnitt, "", FARBE_AKTIV)

        # ECTS (aus DB)
        ects = semester.aktuelle_ects_semester
        wert_ects = str(ects) if ects else "0"
        gesamt_ects = semester.berechne_gesamt_ects()
        self._zeichne_eine_kpi_karte(kpi_frame, 1, "ECTS SEMESTER", wert_ects, f"/ {gesamt_ects} ECTS", FARBE_BLAU)

    def zeige_pflichtmodule_verwaltung(self):
        """Zeigt die Liste aller Pflichtmodule (Zugewiesen vs. Pool)."""
        win = tk.Toplevel(self.root)
        win.title("Pflichtmodule verwalten")
        win.geometry("600x700")
        win.configure(bg=HINTERGRUND_FARBE)

        # Header
        header = tk.Frame(win, bg=HINTERGRUND_FARBE)
        header.pack(fill="x", pady=10, padx=10)
        tk.Button(header, text="← Zurück", command=lambda: [win.destroy(), self.oeffne_modul_verwaltung()],
                  bg="white", relief="flat").pack(side="left")
        tk.Label(header, text="Pflichtmodule", font=SCHRIFT_H2, bg=HINTERGRUND_FARBE).pack(side="left", padx=20)

        # Scrollbarer Bereich
        scroll_area = ScrollableFrame(win, bg=HINTERGRUND_FARBE)
        scroll_area.pack(fill="both", expand=True, padx=10, pady=10)
        content = scroll_area.scrollable_frame

        # Daten holen
        alle_module = self.controller.hole_alle_pflichtmodule()

        # Gruppieren
        zugewiesen_nach_sem = {}
        pool = []

        for mod in alle_module:
            sem_nr = mod.semester_nummer
            if sem_nr is not None:
                if sem_nr not in zugewiesen_nach_sem:
                    zugewiesen_nach_sem[sem_nr] = []
                zugewiesen_nach_sem[sem_nr].append(mod)
            else:
                pool.append(mod)

        # Helper zum Zeichnen einer Zeile
        def zeichne_zeile(parent, mod):
            row = tk.Frame(parent, bg="white", pady=5)
            row.pack(fill="x", pady=2)

            info = f"{mod.name}"
            if mod.code: info += f" ({mod.code})"

            tk.Label(row, text=info, font=SCHRIFT_NORMAL, bg="white", wraplength=350, justify="left").pack(side="left")

            tk.Button(row, text="Bearbeiten", font=SCHRIFT_KLEIN, bg=FARBE_BLAU, fg="white",
                      command=lambda m=mod: self.oeffne_modul_editor(m,
                                                                     callback_nach_speichern=lambda: [win.destroy(),
                                                                                                      self.zeige_pflichtmodule_verwaltung()])).pack(
                side="right")

            tk.Button(row, text="🗑", font=SCHRIFT_KLEIN, bg="#fee2e2", fg="#ef4444",
                      command=lambda m=mod: self.loesche_modul_click(m, callback=lambda: [win.destroy(),
                                                                                          self.zeige_pflichtmodule_verwaltung()])).pack(
                side="right", padx=5)

            tk.Frame(parent, bg=RAHMEN_FARBE, height=1).pack(fill="x")

        # 1. Zugewiesene (nach Semester sortiert)
        if zugewiesen_nach_sem:
            tk.Label(content, text="Im Semester zugewiesen", font=("Helvetica", 12, "bold"), bg=HINTERGRUND_FARBE,
                     fg=FARBE_BLAU).pack(anchor="w", pady=(20, 5))

            for sem_nr in sorted(zugewiesen_nach_sem.keys()):
                sem_frame = tk.LabelFrame(content, text=f" Semester {sem_nr} ", font=("Helvetica", 10, "bold"),
                                          bg="white", fg=TEXT_DUNKEL, padx=10, pady=5)
                sem_frame.pack(fill="x", pady=5, padx=5)

                for mod in zugewiesen_nach_sem[sem_nr]:
                    zeichne_zeile(sem_frame, mod)

        # 2. Pool
        tk.Label(content, text="Nicht zugewiesen (Pool)", font=("Helvetica", 12, "bold"), bg=HINTERGRUND_FARBE,
                 fg=TEXT_DUNKEL).pack(anchor="w", pady=(20, 5))
        if not pool:
            tk.Label(content, text="Keine Module im Pool.", bg=HINTERGRUND_FARBE, fg=TEXT_HELL).pack(anchor="w",
                                                                                                     padx=10)
        else:
            pool_frame = tk.Frame(content, bg="white", padx=10, pady=10)
            pool_frame.pack(fill="x", padx=5)
            for mod in pool:
                zeichne_zeile(pool_frame, mod)

    def zeige_wp_verwaltung(self):
        """Zeigt die Liste aller Wahlpflichtmodule, gruppiert nach Bereich."""
        win = tk.Toplevel(self.root)
        win.title("Wahlpflichtmodule verwalten")
        win.geometry("600x700")
        win.configure(bg=HINTERGRUND_FARBE)

        # Header
        header = tk.Frame(win, bg=HINTERGRUND_FARBE)
        header.pack(fill="x", pady=10, padx=10)
        tk.Button(header, text="← Zurück", command=lambda: [win.destroy(), self.oeffne_modul_verwaltung()],
                  bg="white", relief="flat").pack(side="left")
        tk.Label(header, text="Wahlpflichtmodule", font=SCHRIFT_H2, bg=HINTERGRUND_FARBE).pack(side="left", padx=20)

        # Scrollbarer Bereich
        scroll_area = ScrollableFrame(win, bg=HINTERGRUND_FARBE)
        scroll_area.pack(fill="both", expand=True, padx=10, pady=10)
        content = scroll_area.scrollable_frame

        # Daten holen
        alle_wp = self.controller.hole_alle_wahlpflichtmodule()

        # Gruppieren nach Bereich
        bereiche = {}
        for mod in alle_wp:
            b = mod.wahlpflichtbereich
            if b not in bereiche:
                bereiche[b] = {'zugewiesen': [], 'pool': []}

            if mod.semester_nummer is not None:
                bereiche[b]['zugewiesen'].append(mod)
            else:
                bereiche[b]['pool'].append(mod)

        # Sortierte Bereiche durchgehen (A, B, C...)
        for bereich_name in sorted(bereiche.keys()):
            # Großer Container für den Bereich
            bereich_frame = tk.LabelFrame(content, text=f" Wahlpflichtbereich {bereich_name} ",
                                          font=("Helvetica", 14, "bold"), bg="white", fg=FARBE_VIOLETT, padx=10,
                                          pady=10)
            bereich_frame.pack(fill="x", pady=15, padx=5)

            # Helper für Zeilen
            def zeichne_wp_zeile(parent, mod):
                row = tk.Frame(parent, bg="white", pady=5)
                row.pack(fill="x", pady=2)

                info = f"{mod.name}"
                if mod.code: info += f" ({mod.code})"

                tk.Label(row, text=info, font=SCHRIFT_NORMAL, bg="white", wraplength=350, justify="left").pack(
                    side="left")

                tk.Button(row, text="Bearbeiten", font=SCHRIFT_KLEIN, bg=FARBE_VIOLETT, fg="white",
                          command=lambda m=mod: self.oeffne_modul_editor(m, callback_nach_speichern=lambda: [
                              win.destroy(), self.zeige_wp_verwaltung()])).pack(side="right")

                tk.Button(row, text="🗑", font=SCHRIFT_KLEIN, bg="#fee2e2", fg="#ef4444",
                          command=lambda m=mod: self.loesche_modul_click(m, callback=lambda: [win.destroy(),
                                                                                              self.zeige_wp_verwaltung()])).pack(
                    side="right", padx=5)

                tk.Frame(parent, bg=RAHMEN_FARBE, height=1).pack(fill="x")

            # 1. Zugewiesene
            if bereiche[bereich_name]['zugewiesen']:
                tk.Label(bereich_frame, text="Im Semester zugewiesen:", font=("Helvetica", 10, "bold"),
                         bg="white", fg=TEXT_DUNKEL).pack(anchor="w", pady=(5, 5))
                for mod in bereiche[bereich_name]['zugewiesen']:
                    zeichne_wp_zeile(bereich_frame, mod)

            # 2. Pool
            if bereiche[bereich_name]['pool']:
                tk.Label(bereich_frame, text="Nicht zugewiesen (Pool):", font=("Helvetica", 10, "bold"),
                         bg="white", fg=TEXT_HELL).pack(anchor="w", pady=(15, 5))
                for mod in bereiche[bereich_name]['pool']:
                    zeichne_wp_zeile(bereich_frame, mod)


    #Dialoge

    def oeffne_einstellungen(self):
        """Öffnet ein Fenster zum Bearbeiten der Studiengangs-Details."""
        win = tk.Toplevel(self.root)
        win.title("Studienplan konfigurieren")
        win.geometry("400x500")
        win.configure(bg="white")
        win.transient(self.root)
        win.grab_set()
        container = tk.Frame(win, bg="white", padx=25, pady=20)
        container.pack(fill="both", expand=True)

        tk.Label(container, text="Studien-Konfiguration", font=SCHRIFT_H2, bg="white").pack(pady=(0, 20))

        # Hilfsfunktion für Eingabefelder
        def create_input(label, val):
            tk.Label(container, text=label, font=("Helvetica", 8, "bold"), bg="white", fg=TEXT_HELL).pack(anchor="w")
            ent = tk.Entry(container, font=SCHRIFT_NORMAL, highlightthickness=1, highlightbackground=RAHMEN_FARBE)
            if val is not None:
                ent.insert(0, str(val))
            ent.pack(fill="x", pady=(2, 12))
            return ent

        # Felder mit aktuellen Werten füllen
        e_name = create_input("Name des Studiengangs:", self.studiengang.name)
        e_schnitt = create_input("Ziel-Notenschnitt:", self.studiengang.ziel_notenschnitt)
        e_ects = create_input("ECTS Gesamtzahl:", self.studiengang.ziel_ects)
        beginn_str = self.studiengang.beginn.strftime("%d.%m.%Y") if self.studiengang.beginn else ""
        e_beginn = create_input("Startdatum (TT.MM.JJJJ):", beginn_str)
        e_dauer = create_input("Ziel-Dauer in Monaten:", self.studiengang.ziel_abschlussdauer)

        def speichern():
            daten = {
                'name': e_name.get(),
                'ziel_schnitt': e_schnitt.get(),
                'ziel_ects': e_ects.get(),
                'ziel_dauer': e_dauer.get(),
                'beginn': e_beginn.get()
            }
            self.controller.speichere_studiengang_details(
                daten,
                callback=lambda: [win.destroy(), self.lade_und_zeichne_dashboard()]
            )

        tk.Button(container, text="💾 Speichern", command=speichern,
                  bg=FARBE_BLAU, fg="white", font=("Helvetica", 10, "bold"), pady=10).pack(fill="x", pady=20)

    def oeffne_modul_editor(self, modul=None, semester_id=None, is_wahlpflicht=False, callback_nach_speichern=None):
        """
        Öffnet einen Dialog zum Bearbeiten oder Erstellen eines Moduls.
        Zeigt dynamisch Felder für Prüfungsleistungen an, wenn der Status 'Bestanden'/'Nicht bestanden' ist.
        """
        # HIER WURDE GEÄNDERT: Modul komplett laden, falls ID vorhanden
        if modul:
            geladenes_modul = self.controller.lade_modul(modul.id)
            if geladenes_modul:
                modul = geladenes_modul

        win = tk.Toplevel(self.root)
        win.title("Modul bearbeiten" if modul else "Neues Modul erstellen")
        win.geometry("450x650")
        win.configure(bg="white")
        win.transient(self.root)
        win.grab_set()

        container = tk.Frame(win, bg="white", padx=25, pady=20)
        container.pack(fill="both", expand=True)

        tk.Label(container, text="Modul-Details", font=SCHRIFT_H2, bg="white").pack(pady=(0, 20))

        # --- Hilfsfunktion für Eingabefelder ---
        def create_input(label, val):
            tk.Label(container, text=label, font=("Helvetica", 8, "bold"), bg="white", fg=TEXT_HELL).pack(anchor="w")
            ent = tk.Entry(container, font=SCHRIFT_NORMAL, highlightthickness=1, highlightbackground=RAHMEN_FARBE)
            if val is not None:
                ent.insert(0, str(val))
            ent.pack(fill="x", pady=(2, 12))
            return ent

        # --- 1. Basis-Daten (Immer sichtbar) ---
        e_name = create_input("Modulname:", modul.name if modul else "")
        e_code = create_input("Modulcode:", modul.code if modul else "")
        e_ects = create_input("ECTS:", modul.ects if modul else "")

        # Zeigen, wenn is_wahlpflicht=True ODER wenn es schon ein WP-Modul ist
        ist_wp = is_wahlpflicht or isinstance(modul, WahlpflichtModul)

        bereich_var = tk.StringVar()
        if ist_wp:
            tk.Label(container, text="Wahlpflichtbereich:", font=("Helvetica", 8, "bold"), bg="white",
                     fg=TEXT_HELL).pack(anchor="w")

            # Verfügbare Bereiche laden
            verfuegbare_bereiche = self.controller.hole_verfuegbare_wp_bereiche()
            # Standardvorschläge hinzufügen, falls DB leer
            if not verfuegbare_bereiche:
                verfuegbare_bereiche = WP_BEREICHE

            bereich_combo = ttk.Combobox(container, textvariable=bereich_var, values=verfuegbare_bereiche)
            if isinstance(modul, WahlpflichtModul) and modul.wahlpflichtbereich:
                bereich_combo.set(modul.wahlpflichtbereich)
            bereich_combo.pack(fill="x", pady=(2, 12))

        tk.Label(container, text="Status:", font=("Helvetica", 8, "bold"), bg="white", fg=TEXT_HELL).pack(anchor="w")
        status_var = tk.StringVar(value=modul.status if modul else "Geplant")
        status_combo = ttk.Combobox(container, textvariable=status_var, values=ALLE_MODUL_STATUS, state="readonly")
        status_combo.pack(fill="x", pady=(2, 12))

        # --- Warn-Label für Statuswechsel ---
        warn_label = tk.Label(container, text="⚠️ Achtung: Prüfungsleistung wird gelöscht!",
                              font=("Helvetica", 8, "bold"), bg="white", fg="#ef4444")
        # Standardmäßig versteckt, wird in update_ui gezeigt

        # --- 2. Dynamischer Bereich für Prüfungsleistungen ---
        pruefung_frame = tk.Frame(container, bg="white")
        pruefung_frame.pack(fill="x", pady=(10, 0))

        # Variablen für Prüfungsdaten (müssen hier definiert sein, damit update_ui sie kennt)
        widgets_pruefung = {}

        def update_ui(event=None):
            """Zeigt oder versteckt die Prüfungsfelder basierend auf dem Status."""
            # Alten Inhalt löschen
            for widget in pruefung_frame.winfo_children():
                widget.destroy()
            widgets_pruefung.clear()

            status = status_var.get()

            # Warn-Logik
            ursprung_status = modul.status if modul else "Geplant"
            if ursprung_status in [STATUS_BESTANDEN, STATUS_NICHT_BESTANDEN] and status not in [STATUS_BESTANDEN, STATUS_NICHT_BESTANDEN]:
                warn_label.pack(pady=(5, 0))
            else:
                warn_label.pack_forget()

            if status in [STATUS_BESTANDEN, STATUS_NICHT_BESTANDEN]:
                tk.Label(pruefung_frame, text="Prüfungsleistung", font=("Helvetica", 10, "bold"), bg="white",
                         fg=TEXT_DUNKEL).pack(anchor="w", pady=(10, 5))

                # Prüfungsart
                tk.Label(pruefung_frame, text="Prüfungsart:", font=("Helvetica", 8, "bold"), bg="white",
                         fg=TEXT_HELL).pack(anchor="w")
                art_var = tk.StringVar(value=modul.hole_pruefungsart() if modul else "Klausur")
                art_combo = ttk.Combobox(pruefung_frame, textvariable=art_var, values=MOEGLICHE_PRUEFUNGSARTEN,
                                         state="readonly")
                art_combo.pack(fill="x", pady=(2, 10))
                widgets_pruefung['pruefungsart'] = art_var

                # Note & Punkte (Nebeneinander)
                row1 = tk.Frame(pruefung_frame, bg="white")
                row1.pack(fill="x")

                tk.Label(row1, text="Note:", font=("Helvetica", 8, "bold"), bg="white", fg=TEXT_HELL).pack(side="left")
                e_note = tk.Entry(row1, width=10, font=SCHRIFT_NORMAL, highlightthickness=1,
                                  highlightbackground=RAHMEN_FARBE)
                val_note = modul.hole_note() if modul else ""
                if val_note: e_note.insert(0, str(val_note))
                e_note.pack(side="left", padx=(5, 20))
                widgets_pruefung['note'] = e_note

                tk.Label(row1, text="Punkte:", font=("Helvetica", 8, "bold"), bg="white", fg=TEXT_HELL).pack(
                    side="left")
                e_punkte = tk.Entry(row1, width=10, font=SCHRIFT_NORMAL, highlightthickness=1,
                                    highlightbackground=RAHMEN_FARBE)
                val_punkte = modul.hole_punkte() if modul else ""
                if val_punkte: e_punkte.insert(0, str(val_punkte))
                e_punkte.pack(side="left", padx=5)
                widgets_pruefung['punkte'] = e_punkte

                # Datum & Versuch (Nebeneinander)
                row2 = tk.Frame(pruefung_frame, bg="white", pady=10)
                row2.pack(fill="x")

                tk.Label(row2, text="Datum:", font=("Helvetica", 8, "bold"), bg="white", fg=TEXT_HELL).pack(side="left")
                e_datum = tk.Entry(row2, width=12, font=SCHRIFT_NORMAL, highlightthickness=1,
                                   highlightbackground=RAHMEN_FARBE)
                val_datum = modul.hole_datum() if modul else ""
                if val_datum: e_datum.insert(0, val_datum.strftime("%d.%m.%Y"))
                e_datum.pack(side="left", padx=(5, 20))
                widgets_pruefung['datum'] = e_datum

                tk.Label(row2, text="Versuch:", font=("Helvetica", 8, "bold"), bg="white", fg=TEXT_HELL).pack(
                    side="left")
                e_versuch = tk.Entry(row2, width=5, font=SCHRIFT_NORMAL, highlightthickness=1,
                                     highlightbackground=RAHMEN_FARBE)
                val_versuch = modul.hole_versuch() if modul else "1"
                if val_versuch is not None:
                    e_versuch.insert(0, str(val_versuch))
                e_versuch.pack(side="left", padx=5)
                widgets_pruefung['versuch'] = e_versuch

        # Event binden
        status_combo.bind("<<ComboboxSelected>>", update_ui)

        # Initial aufrufen
        update_ui()

        def speichern():
            # --- 1. Daten sammeln (ohne Validierung in GUI) ---
            basis_daten = {
                'name': e_name.get(),
                'code': e_code.get(),
                'ects': e_ects.get(),
                'status': status_var.get(),
                'semester_id': semester_id
            }

            if ist_wp:
                basis_daten['bereich'] = bereich_var.get()

            pruef_daten = None
            if status_var.get() in [STATUS_BESTANDEN, STATUS_NICHT_BESTANDEN]:
                pruef_daten = {
                    'pruefungsart': widgets_pruefung['pruefungsart'].get(),
                    'note': widgets_pruefung['note'].get(),
                    'punkte': widgets_pruefung['punkte'].get(),
                    'datum': widgets_pruefung['datum'].get(),
                    'versuch': widgets_pruefung['versuch'].get()
                }

            # --- 2. Navigation nach Erfolg definieren und an Controller übergeben ---
            def nach_erfolg():
                win.destroy()
                if callback_nach_speichern:
                    callback_nach_speichern()
                elif modul and modul.semester_id:
                    self.zeige_semester_detail(modul.semester_id)
                elif semester_id:
                    self.zeige_semester_detail(semester_id)
                else:
                    self.lade_und_zeichne_dashboard()

            self.controller.speichere_modul(basis_daten, pruef_daten, modul.id if modul else None, callback=nach_erfolg)

        tk.Button(container, text="💾 Speichern", command=speichern,
                  bg=FARBE_BLAU, fg="white", font=("Helvetica", 10, "bold"), pady=10).pack(fill="x", pady=20)

    def oeffne_modul_verwaltung(self):
        """Öffnet das Auswahl-Fenster für die Modul-Verwaltung."""
        win = tk.Toplevel(self.root)
        win.title("Modul-Verwaltung")
        win.geometry("400x300")
        win.configure(bg="white")
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="Modul-Verwaltung", font=SCHRIFT_H2, bg="white").pack(pady=20)

        tk.Button(win, text="Pflichtmodule verwalten",
                  command=lambda: [win.destroy(), self.zeige_pflichtmodule_verwaltung()],
                  bg=FARBE_BLAU, fg="white", font=SCHRIFT_NORMAL, width=25, pady=10).pack(pady=10)

        tk.Button(win, text="Wahlpflichtmodule verwalten",
                  command=lambda: [win.destroy(), self.zeige_wp_verwaltung()],
                  bg=FARBE_VIOLETT, fg="white", font=SCHRIFT_NORMAL, width=25, pady=10).pack(pady=10)

    def oeffne_modul_hinzufuegen_dialog(self, semester_id):
        """Schritt 1: Auswahl Pflicht oder Wahlpflicht."""
        win = tk.Toplevel(self.root)
        win.title("Modul hinzufügen")
        win.geometry("400x300")
        win.configure(bg="white")
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="Was möchtest du hinzufügen?", font=SCHRIFT_H2, bg="white").pack(pady=20)

        tk.Button(win, text="Pflichtmodul",
                  command=lambda: [win.destroy(), self.oeffne_modul_typ_auswahl("Pflicht", semester_id)],
                  bg=FARBE_BLAU, fg="white", font=SCHRIFT_NORMAL, width=25, pady=10).pack(pady=10)

        tk.Button(win, text="Wahlpflichtmodul",
                  command=lambda: [win.destroy(), self.oeffne_modul_typ_auswahl("Wahlpflicht", semester_id)],
                  bg=FARBE_VIOLETT, fg="white", font=SCHRIFT_NORMAL, width=25, pady=10).pack(pady=10)

    def oeffne_pool_auswahl_liste(self, typ, semester_id):
        """Schritt 3: Liste der freien Module zum Auswählen."""
        win = tk.Toplevel(self.root)
        win.title(f"Freie {typ}module")
        win.geometry("500x600")
        win.configure(bg=HINTERGRUND_FARBE)
        win.transient(self.root)
        win.grab_set()

        # Header mit Zurück
        header = tk.Frame(win, bg=HINTERGRUND_FARBE)
        header.pack(fill="x", pady=10, padx=10)
        tk.Button(header, text="← Zurück",
                  command=lambda: [win.destroy(), self.oeffne_modul_typ_auswahl(typ, semester_id)],
                  bg="white", relief="flat").pack(side="left")
        tk.Label(header, text=f"Freie {typ}module", font=SCHRIFT_H2, bg=HINTERGRUND_FARBE).pack(side="left", padx=20)

        # Scrollbarer Bereich
        scroll_area = ScrollableFrame(win, bg=HINTERGRUND_FARBE)
        scroll_area.pack(fill="both", expand=True, padx=10, pady=10)
        content = scroll_area.scrollable_frame

        # Daten holen (nur die ohne Semester!)
        if typ == "Pflicht":
            freie_module = self.controller.hole_alle_pflichtmodule(nur_freie=True)
        else:
            freie_module = self.controller.hole_alle_wahlpflichtmodule(nur_freie=True)

        if not freie_module:
            tk.Label(content, text="Keine freien Module im Pool gefunden.", bg=HINTERGRUND_FARBE, fg=TEXT_HELL).pack(
                pady=20)
            return

        # Helper für Zuweisung
        def zuweisen(mod_id):
            self.controller.weise_modul_semester_zu(
                mod_id,
                semester_id,
                callback=lambda: [win.destroy(), self.zeige_semester_detail(semester_id)]
            )

        # Liste zeichnen
        if typ == "Wahlpflicht":
            bereiche = {}
            for mod in freie_module:
                b = mod.wahlpflichtbereich
                if b not in bereiche: bereiche[b] = []
                bereiche[b].append(mod)

            for b_name in sorted(bereiche.keys()):
                tk.Label(content, text=f"Bereich {b_name}", font=("Helvetica", 10, "bold"), bg=HINTERGRUND_FARBE,
                         fg=FARBE_VIOLETT).pack(anchor="w", pady=(10, 5))
                for mod in bereiche[b_name]:
                    btn = tk.Button(content, text=f"{mod.name} ({mod.code or '-'})",
                                    command=lambda m_id=mod.id: zuweisen(m_id),
                                    bg="white", relief="flat", anchor="w", padx=10)
                    btn.pack(fill="x", pady=1)
        else:
            # Pflichtmodule einfach als Liste
            for mod in freie_module:
                btn = tk.Button(content, text=f"{mod.name} ({mod.code or '-'})",
                                command=lambda m_id=mod.id: zuweisen(m_id),
                                bg="white", relief="flat", anchor="w", padx=10)
                btn.pack(fill="x", pady=1)

    def oeffne_modul_typ_auswahl(self, typ, semester_id):
        """Schritt 2: Neu erstellen oder aus Pool."""
        win = tk.Toplevel(self.root)
        win.title(f"{typ}modul hinzufügen")
        win.geometry("400x350")
        win.configure(bg="white")
        win.transient(self.root)
        win.grab_set()

        # Header mit Zurück
        header = tk.Frame(win, bg="white")
        header.pack(fill="x", pady=10, padx=10)
        tk.Button(header, text="← Zurück",
                  command=lambda: [win.destroy(), self.oeffne_modul_hinzufuegen_dialog(semester_id)],
                  bg="white", relief="flat").pack(side="left")

        tk.Label(win, text=f"{typ}modul", font=SCHRIFT_H2, bg="white").pack(pady=10)
        is_wp = (typ == "Wahlpflicht")

        # Option 1: Neu erstellen
        tk.Button(win, text="✨ Neues Modul erstellen",
                  command=lambda: [win.destroy(),
                                   self.oeffne_modul_editor(modul=None, semester_id=semester_id, is_wahlpflicht=is_wp)],
                  bg=FARBE_AKTIV, fg="white", font=SCHRIFT_NORMAL, width=30, pady=10).pack(pady=10)

        tk.Label(win, text="- ODER -", bg="white", fg=TEXT_HELL).pack(pady=5)

        # Option 2: Aus Pool
        tk.Button(win, text="📦 Aus Pool auswählen",
                  command=lambda: [win.destroy(), self.oeffne_pool_auswahl_liste(typ, semester_id)],
                  bg=TEXT_DUNKEL, fg="white", font=SCHRIFT_NORMAL, width=30, pady=10).pack(pady=10)

    def oeffne_testdaten_dialog(self):
        """Fragt den Nutzer und lädt dann die Testdaten."""
        if not messagebox.askyesno("Testdaten laden",
                               "Möchtest du das System auf die Testdaten zurücksetzen?\n\nAktuelle Daten werden überschrieben."):
            return
        self.controller.testdaten_laden()


    def oeffne_db_leeren_dialog(self):
        """Fragt den Nutzer und leert dann die Datenbank."""
        if not messagebox.askyesno("Datenbank leeren",
                               "Möchtest du wirklich ALLE Daten löschen?\n\nDie Datenbank wird komplett geleert."):
            return
        self.controller.datenbank_leeren()

    #Event-Handling
    def _add_semester(self):
        """Delegiert das Hinzufügen eines neuen Semesters an den Controller."""
        self.controller.neues_semester_erstellen()

    def _remove_semester(self):
        """Entfernt das letzte Semester nach Bestätigung."""
        if messagebox.askyesno("Löschen", "Letztes Semester wirklich löschen?"):
            self.controller.letztes_semester_loeschen()

    def loesche_modul_click(self, modul, callback=None):
        """Löscht ein Modul endgültig aus der Datenbank."""
        if messagebox.askyesno("Modul löschen", f"Möchtest du das Modul '{modul.name}' wirklich endgültig löschen?"):
            self.controller.modul_loeschen(modul.id, callback)

    def entferne_modul_aus_semester_click(self, modul):
        """Entfernt ein Modul aus dem Semester (bleibt im Pool)."""
        if messagebox.askyesno("Aus Semester entfernen", f"Soll das Modul '{modul.name}' aus dem Semester entfernt werden?\n(Es bleibt im System erhalten)"):
            self.controller.modul_aus_semester_entfernen(modul.id)

    def exportiere_csv(self):
        """Exportiert die Daten als CSV."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile="Studium_Backup.csv"
        )
        if not file_path:
            return
        self.controller.exportiere_csv(file_path)