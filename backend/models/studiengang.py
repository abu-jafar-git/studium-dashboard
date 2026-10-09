from datetime import date
from typing import List, Optional
from backend.models.semester import Semester
from backend.models.constants import STATUS_MIT_PRUEFUNGSLEISTUNG


class Studiengang:
    """
    Repräsentiert einen Studiengang. Diese Klasse ist ein Daten-Container für die
    in der Datenbank gespeicherten Werte und bietet Methoden zur Neuberechnung.
    """

    def __init__(self, name: str = "Neuer Studiengang", id: Optional[int] = None,
                 ziel_notenschnitt: Optional[float] = None, ziel_ects: Optional[int] = None,
                 beginn: Optional[date] = None, ziel_abschlussdauer: Optional[int] = None,
                 aktuelle_notenschnitt: Optional[float] = 0.0, aktuelle_ects: Optional[int] = 0,
                 aktuelle_zeit_in_monat: Optional[int] = 0, gesamte_module: Optional[int] = 0,
                 abgeschlossene_module: Optional[int] = 0):
        """
        Initialisiert einen neuen Studiengang mit allen Attributen, die einer
        Zeile in der 'studiengang'-Tabelle entsprechen.
        """
        # Ziel-Werte (vom Benutzer gesetzt)
        self.id = id
        self.name = name
        self.ziel_notenschnitt = ziel_notenschnitt
        self.ziel_ects = ziel_ects
        self.beginn = beginn
        self.ziel_abschlussdauer = ziel_abschlussdauer

        # Berechnete Werte (von der DB gelesen)
        self.aktuelle_notenschnitt = aktuelle_notenschnitt
        self.aktuelle_ects = aktuelle_ects
        self.aktuelle_zeit_in_monat = aktuelle_zeit_in_monat
        self.gesamte_module = gesamte_module
        self.abgeschlossene_module = abgeschlossene_module

        # Kompositions-Beziehung: Liste der zugehörigen Semester-Objekte
        self.semester_liste: List[Semester] = []

    def verknuepfe_semester(self, semester: Semester):
        """
        (Intern) Fügt ein bereits erstelltes Semester-Objekt zur internen Liste hinzu.
        Wird typischerweise vom DBManager beim Laden der Daten verwendet.
        """
        self.semester_liste.append(semester)

    def erstelle_neues_semester(self) -> Semester:
        """
        Erstellt ein neues Semester basierend auf dem aktuellen Zustand (nächste Nummer),
        fügt es der internen Liste hinzu und gibt das neue Objekt zurück.
        Dies ist die primäre Methode für die Geschäftslogik.
        """
        naechste_nummer = len(self.semester_liste) + 1
        neues_semester = Semester(nummer=naechste_nummer, studiengang_id=self.id)
        self.semester_liste.append(neues_semester)
        return neues_semester

    def hole_letztes_semester_zum_loeschen(self) -> Semester:
        """
        Prüft, ob das letzte Semester gelöscht werden kann und gibt es zurück.
        Wirft einen ValueError, wenn die Bedingungen nicht erfüllt sind.
        """
        if not self.semester_liste:
            raise ValueError("Keine Semester vorhanden, das gelöscht werden könnten.")

        letztes_semester = self.semester_liste[-1]

        if letztes_semester.module:
            raise ValueError(f"Semester {letztes_semester.nummer} enthält noch Module und kann nicht gelöscht werden.")

        return letztes_semester

    def berechne_gesamt_module(self) -> int:
        """
        Zählt alle Module des Studiengangs über alle Semester.
        """
        return sum(len(s.module) for s in self.semester_liste)

    def aktualisiere_kpis(self) -> None:
        """
        Berechnet alle Studiengang-KPIs neu und schreibt sie in die eigenen Attribute.
        Semester-KPIs sind nicht enthalten – dafür ist Semester.aktualisiere_kpis() zuständig.
        """
        self.aktuelle_notenschnitt = self.berechne_notenschnitt()
        self.aktuelle_ects = self.berechne_ects_fortschritt()
        self.aktuelle_zeit_in_monat = self.berechne_zeitverlauf()
        self.abgeschlossene_module = self.berechne_modul_fortschritt()
        self.gesamte_module = self.berechne_gesamt_module()

    # --- Interne Berechnungsmethoden ---

    def berechne_notenschnitt(self) -> float:
        """
        Berechnet den Notendurchschnitt über alle benoteten Module.
        """
        summe_aller_noten = 0.0
        anzahl_noten = 0
        for semester in self.semester_liste:
            for modul in semester.module:
                if modul.status in STATUS_MIT_PRUEFUNGSLEISTUNG:
                    leistung = modul.hole_leistung()
                    if leistung and leistung.note is not None:
                        summe_aller_noten += leistung.note
                        anzahl_noten += 1
        return summe_aller_noten / anzahl_noten if anzahl_noten > 0 else 0.0

    def berechne_ects_fortschritt(self) -> int:
        """
        Summiert die ECTS-Punkte aller bestandenen Module.
        """
        summe_ects = 0
        for semester in self.semester_liste:
            for modul in semester.module:
                if modul.ist_bestanden():
                    summe_ects += modul.ects
        return summe_ects

    def berechne_zeitverlauf(self) -> int:
        """
        Berechnet die Anzahl der Monate, die seit dem Studienbeginn vergangen sind.
        """
        if not self.beginn:
            return 0
        heute = date.today()
        vergangene_monate = (heute.year - self.beginn.year) * 12 + (heute.month - self.beginn.month)
        return max(0, vergangene_monate)

    def berechne_modul_fortschritt(self) -> int:
        """
        Zählt die Anzahl aller Module, die den Status 'Bestanden' haben.
        """
        anzahl_bestanden = 0
        for semester in self.semester_liste:
            for modul in semester.module:
                if modul.ist_bestanden():
                    anzahl_bestanden += 1
        return anzahl_bestanden
