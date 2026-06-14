from typing import Optional
from datetime import date


class Pruefungsleistung:
    """
    Repräsentiert eine erbrachte oder geplante Prüfungsleistung.
    Diese Klasse ist ein reiner Daten-Container und enthält keine eigene Logik.
    Ihre Attribute werden vom DBManager befüllt.
    """

    def __init__(self, modul_id: int, id: Optional[int] = None,
                 punkte: Optional[float] = None, note: Optional[float] = None,
                 datum: Optional[date] = None, versuch: Optional[int] = None,
                 pruefungsart: Optional[str] = None):
        """
        Initialisiert eine neue Prüfungsleistung.

        :param modul_id: Die ID des zugehörigen Moduls. Dies ist das einzige Pflichtfeld.
        :param id: Die eindeutige ID aus der Datenbank.
        :param punkte: Die erreichten Punkte (z.B. 0-100).
        :param note: Die erreichte Note (z.B. 1.0 - 5.0).
        :param datum: Das Datum der Prüfung.
        :param versuch: Der wievielte Versuch es war.
        :param pruefungsart: Die Art der Prüfung (z.B. 'Klausur').
        """
        self.modul_id = modul_id
        self.id = id
        self.punkte = punkte
        self.note = note
        self.datum = datum
        self.versuch = versuch
        self.pruefungsart = pruefungsart

