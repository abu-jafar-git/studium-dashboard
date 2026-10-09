from typing import Optional
from datetime import date
from backend.models.pruefungsleistung import Pruefungsleistung
from backend.models.constants import STATUS_BESTANDEN, STATUS_MIT_PRUEFUNGSLEISTUNG


class Modul:
    """
    Repräsentiert ein Studienmodul.
    Diese Klasse dient als Basis für alle Arten von Modulen und kapselt die
    Beziehung zu einer einzelnen, optionalen Prüfungsleistung.
    """

    def __init__(self, name: str, id: Optional[int] = None, semester_id: Optional[int] = None,
                 code: Optional[str] = None, ects: Optional[int] = None, status: Optional[str] = None,
                 semester_nummer: Optional[int] = None):
        """
        Initialisiert ein neues Modul-Objekt.

        :param name: Der Name des Moduls (einziges Pflichtfeld).
        :param id: Die eindeutige ID aus der Datenbank.
        :param semester_id: Die ID des zugehörigen Semesters (wenn es zugeordnet ist).
        :param code: Der eindeutige Modul-Code (z.B. "CS101").
        :param ects: Die Anzahl der ECTS-Punkte für dieses Modul.
        :param status: Der aktuelle Status (z.B. "Geplant", "Bestanden").
        """
        self.name = name
        self.id = id
        self.semester_id = semester_id
        self.semester_nummer = semester_nummer
        self.code = code
        self.ects = ects
        self.status = status
        self.pruefungsleistung: Optional[Pruefungsleistung] = None

    def setze_leistung(self, leistung: Pruefungsleistung):
        """
        Verknüpft ein Prüfungsleistungs-Objekt mit diesem Modul.

        :param leistung: Das Prüfungsleistungs-Objekt, das verknüpft werden soll.
        """
        self.pruefungsleistung = leistung

    def ist_bestanden(self) -> bool:
        """
        Prüft, ob der Status des Moduls 'Bestanden' ist.

        :return: True, wenn der Status 'Bestanden' ist, ansonsten False.
        """
        return self.status == STATUS_BESTANDEN

    def pruefe_ob_loeschbar(self):
        """
        Geschäftsregel: Prüft, ob das Modul gelöscht werden darf.
        Löst einen ValueError aus, wenn die Regel verletzt wird.
        """
        if self.status in STATUS_MIT_PRUEFUNGSLEISTUNG:
            raise ValueError("Bestandene oder nicht bestandene Module können nicht gelöscht werden.")

    def ist_frei(self) -> bool:
        """
        Gibt an, ob das Modul noch keinem Semester zugeordnet ist.
        """
        return self.semester_id is None

    def soll_pruefungsleistung_loeschen(self) -> bool:
        """
        Geschäftsregel: Gibt an, ob beim Speichern eine vorhandene Prüfungsleistung
        gelöscht werden soll. Das ist der Fall, wenn der Status weder 'Bestanden'
        noch 'Nicht bestanden' ist.
        """
        return self.status not in STATUS_MIT_PRUEFUNGSLEISTUNG

    #Getter-Methoden für gekapselte Daten der Prüfungsleistung

    def hole_leistung(self) -> Optional[Pruefungsleistung]:
        """
        Gibt das gesamte verknüpfte Prüfungsleistungs-Objekt zurück.
        Dies dient als "Generalschlüssel", falls alle Details auf einmal benötigt werden.

        :return: Das Prüfungsleistungs-Objekt oder None.
        """
        return self.pruefungsleistung

    def hole_punkte(self) -> Optional[float]:
        """
        Gibt die Punkte der verknüpften Prüfungsleistung sicher zurück.

        :return: Die erreichten Punkte als float oder None.
        """
        return self.pruefungsleistung.punkte if self.pruefungsleistung else None

    def hole_note(self) -> Optional[float]:
        """
        Gibt die Note der verknüpften Prüfungsleistung sicher zurück.

        :return: Die Note als float oder None.
        """
        return self.pruefungsleistung.note if self.pruefungsleistung else None

    def hole_datum(self) -> Optional[date]:
        """
        Gibt das Datum der verknüpften Prüfungsleistung sicher zurück.

        :return: Das Prüfungsdatum als date-Objekt oder None.
        """
        return self.pruefungsleistung.datum if self.pruefungsleistung else None

    def hole_versuch(self) -> Optional[int]:
        """
        Gibt den Versuch der verknüpften Prüfungsleistung sicher zurück.

        :return: Die Versuchsnummer als int oder None.
        """
        return self.pruefungsleistung.versuch if self.pruefungsleistung else None

    def hole_pruefungsart(self) -> Optional[str]:
        """
        Gibt die Prüfungsart der verknüpften Prüfungsleistung sicher zurück.

        :return: Die Prüfungsart als string oder None.
        """
        return self.pruefungsleistung.pruefungsart if self.pruefungsleistung else None


class WahlpflichtModul(Modul):
    """
    Repräsentiert ein Wahlpflichtmodul.
    Diese Klasse erbt alle Eigenschaften und Methoden von Modul und
    fügt lediglich das Attribut für den Wahlpflichtbereich hinzu.
    """

    def __init__(self, name: str, id: Optional[int] = None, semester_id: Optional[int] = None,
                 code: Optional[str] = None, ects: Optional[int] = None, status: Optional[str] = None,
                 wahlpflichtbereich: Optional[str] = None, semester_nummer: Optional[int] = None):
        """
        Initialisiert ein neues Wahlpflichtmodul.

        :param wahlpflichtbereich: Die Kategorie des Wahlpflichtmoduls (z.B. 'A', 'B').
        (Alle anderen Parameter sind identisch zu Modul).
        """
        super().__init__(name, id, semester_id, code, ects, status, semester_nummer)
        self.wahlpflichtbereich = wahlpflichtbereich
