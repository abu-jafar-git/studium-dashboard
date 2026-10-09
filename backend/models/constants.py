"""
Zentrale Konfiguration für Farben, Schriftarten und Status-Texte.
Dient als einfaches Design-System für die gesamte Anwendung.
"""

# --- Farben
HINTERGRUND_FARBE = "#f8fafc"   # Helles Grau für den App-Hintergrund
KARTE_HINTERGRUND = "#ffffff"   # Weiß für Karten/Container
TEXT_DUNKEL = "#1e293b"         # Dunkles Grau für Haupttexte
TEXT_HELL = "#64748b"           # Mittelgrau für Labels/Subtexte
RAHMEN_FARBE = "#e2e8f0"        # Dezente Rahmenfarbe

# Status-Farben
FARBE_BESTANDEN = "#10b981"     # Grün
FARBE_AKTIV = "#fbbf24"         # Gelb/Orange
FARBE_NICHT_BESTANDEN = "#ef4444" # Rot
FARBE_GEPLANT = "#cbd5e1"       # Grau

# Akzentfarben für UI-Elemente
FARBE_BLAU = "#3b82f6"
FARBE_INDIGO = "#6366f1"
FARBE_VIOLETT = "#8b5cf6"

# --- SCHRIFTARTEN ---
SCHRIFT_TITEL = ("Helvetica", 20, "bold")
SCHRIFT_H2 = ("Helvetica", 14, "bold")
SCHRIFT_KPI_WERT = ("Helvetica", 24, "bold")
SCHRIFT_KPI_LABEL = ("Helvetica", 8, "bold")
SCHRIFT_NORMAL = ("Helvetica", 10)
SCHRIFT_KLEIN = ("Helvetica", 9)

# --- STATUS-KONSTANTEN (Semester) ---
STATUS_AKTIV = "Aktiv"
STATUS_NICHT_AKTIV = "Nicht aktiv"

# --- STATUS-KONSTANTEN (Modul) ---
STATUS_BESTANDEN = "Bestanden"
STATUS_NICHT_BESTANDEN = "Nicht bestanden"
STATUS_IN_ARBEIT = "In Arbeit"
STATUS_GEPLANT = "Geplant"

# Liste aller Status-Optionen für Dropdowns
ALLE_MODUL_STATUS = [STATUS_GEPLANT, STATUS_IN_ARBEIT, STATUS_BESTANDEN, STATUS_NICHT_BESTANDEN]
STATUS_MIT_PRUEFUNGSLEISTUNG = [STATUS_BESTANDEN, STATUS_NICHT_BESTANDEN]

# Mapping: Welcher Status hat welche Farbe?
STATUS_FARBEN = {
    STATUS_BESTANDEN: FARBE_BESTANDEN,
    STATUS_IN_ARBEIT: FARBE_AKTIV,
    STATUS_NICHT_BESTANDEN: FARBE_NICHT_BESTANDEN,
    STATUS_GEPLANT: FARBE_GEPLANT
}

# --- GESCHÄFTSREGELN (Prüfungsleistung) ---
MOEGLICHE_VERSUCHE = [1, 2, 3]

MOEGLICHE_PRUEFUNGSARTEN = [
    "Klausur",
    "Hausarbeit",
    "Workbook",
    "Projektbericht",
    "Fallstudie",
    "Portfolio",
    "Bachelorarbeit",
    "Kolloquium"
]

# --- GESCHÄFTSREGELN (Wahlpflicht) ---
WP_BEREICHE = ["A", "B", "C"]
