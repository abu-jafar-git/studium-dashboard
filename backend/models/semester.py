from typing import List, Optional
from backend.models.modul import Modul
from backend.models.constants import STATUS_BESTANDEN, STATUS_NICHT_BESTANDEN


class Semester:
    """
    Repräsentiert ein Semester innerhalb eines Studiengangs.
    Diese Klasse ist ein Daten-Container für die in der Datenbank gespeicherten
    Werte und enthält die Liste der zugehörigen Module.
    """

    def __init__(self, nummer: int, id: Optional[int] = None, studiengang_id: Optional[int] = None,
                 ist_aktiv: bool = False, notenschnitt_semester: Optional[float] = None,
                 aktuelle_ects_semester: Optional[int] = 0, gesamt_ects_semester: Optional[int] = 0):
        """
        Initialisiert ein neues Semester-Objekt.

        :param nummer: Die Nummer des Semesters (z.B. 1, 2, 3).
        :param id: Die eindeutige ID aus der Datenbank.
        :param studiengang_id: Die ID des zugehörigen Studiengangs.
        :param ist_aktiv: Gibt an, ob dies das aktuell aktive Semester ist.
        :param notenschnitt_semester: Der berechnete Notenschnitt nur für dieses Semester.
        :param aktuelle_ects_semester: Die berechnete Summe der ECTS nur für dieses Semester.
        :param gesamt_ects_semester: Die Summe der ECTS aller Module dieses Semesters (unabhängig vom Status).
        """
        self.id = id
        self.studiengang_id = studiengang_id
        self.nummer = nummer
        self.ist_aktiv = ist_aktiv

        # Berechnete Werte
        self.notenschnitt_semester = notenschnitt_semester
        self.aktuelle_ects_semester = aktuelle_ects_semester
        self.gesamt_ects_semester = gesamt_ects_semester

        # Aggregations-Beziehung: Liste der zugehörigen Modul-Objekte
        self.module: List[Modul] = []

    def aktualisiere_kpis(self) -> None:
        """
        Berechnet alle Semester-KPIs neu und schreibt sie in die eigenen Attribute.
        """
        self.notenschnitt_semester = self.berechne_semester_schnitt()
        self.aktuelle_ects_semester = self.berechne_semester_ects()
        self.gesamt_ects_semester = self.berechne_gesamt_ects()

    def berechne_semester_schnitt(self) -> float:
        """
        Berechnet den Notendurchschnitt.
        Berücksichtigt Module mit Status 'Bestanden' oder 'Nicht bestanden'.
        """
        summe_noten = 0.0
        anzahl_noten = 0

        for modul in self.module:
            # 1. Status prüfen
            if modul.status in [STATUS_BESTANDEN, STATUS_NICHT_BESTANDEN]:
                # 2. Note holen (aus dem verknüpften Objekt)
                note = modul.hole_note()

                # 3. Wenn Note vorhanden, addieren
                if note is not None:
                    summe_noten += note
                    anzahl_noten += 1

        return summe_noten / anzahl_noten if anzahl_noten > 0 else 0.0

    def berechne_semester_ects(self) -> int:
        """
        Summiert die ECTS-Punkte.
        Berücksichtigt NUR Module mit Status 'Bestanden'.
        """
        summe_ects = 0
        for modul in self.module:
            if modul.status == STATUS_BESTANDEN:
                summe_ects += modul.ects
        return summe_ects

    def berechne_gesamt_ects(self) -> int:
        """
        Summiert die ECTS-Punkte aller Module im Semester, unabhängig vom Status.
        """
        return sum(modul.ects for modul in self.module if modul.ects)