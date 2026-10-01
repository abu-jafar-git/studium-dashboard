from typing import List, Dict, Any
from datetime import datetime
from backend.models.constants import ALLE_MODUL_STATUS, MOEGLICHE_VERSUCHE


class StudiengangValidator:
    """
    Validator für Studiengang-Daten.
    Kapselt alle Geschäftsregeln für die Studiengang-Validierung.
    """

    @staticmethod
    def validiere(daten: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validiert Studiengang-Daten.

        :param daten: Dictionary mit Studiengang-Daten
        :return: (ist_gueltig: bool, fehler: List[str])
        """
        fehler = []

        # Name
        if not daten.get('name') or not daten.get('name').strip():
            fehler.append("- Studiengangsname darf nicht leer sein.")

        # Ziel-Notenschnitt
        try:
            ziel_schnitt = float(str(daten.get('ziel_schnitt', '0')).replace(',', '.'))
            if not (1.0 <= ziel_schnitt <= 6.0):
                fehler.append("- Ziel-Notenschnitt muss zwischen 1.0 und 6.0 liegen.")
        except (ValueError, TypeError):
            fehler.append("- Ziel-Notenschnitt muss eine Zahl sein.")

        # Ziel-ECTS
        try:
            ziel_ects = int(daten.get('ziel_ects', 0))
            if ziel_ects <= 0:
                fehler.append("- Ziel-ECTS muss größer als 0 sein.")
        except (ValueError, TypeError):
            fehler.append("- Ziel-ECTS muss eine ganze Zahl sein.")

        # Ziel-Abschlussdauer
        try:
            ziel_dauer = int(daten.get('ziel_dauer', 0))
            if ziel_dauer <= 0:
                fehler.append("- Ziel-Abschlussdauer muss größer als 0 sein.")
        except (ValueError, TypeError):
            fehler.append("- Ziel-Abschlussdauer muss eine ganze Zahl sein.")

        # Beginn-Datum
        beginn_str = daten.get('beginn')
        if beginn_str:
            try:
                datetime.strptime(beginn_str, '%d.%m.%Y')
            except ValueError:
                fehler.append("- Beginn-Datum muss im Format TT.MM.JJJJ sein.")

        return len(fehler) == 0, fehler


class ModulValidator:
    """
    Validator für Modul-Daten.
    Kapselt alle Geschäftsregeln für die Modul-Validierung.
    """

    @staticmethod
    def validiere(daten: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validiert Modul-Daten.

        :param daten: Dictionary mit Modul-Daten
        :return: (ist_gueltig: bool, fehler: List[str])
        """
        fehler = []

        # Name
        if not daten.get('name') or not daten.get('name').strip():
            fehler.append("- Modulname darf nicht leer sein.")

        # ECTS
        try:
            ects = int(daten.get('ects', 0))
            if ects <= 0:
                fehler.append("- ECTS muss größer als 0 sein.")
        except (ValueError, TypeError):
            fehler.append("- ECTS muss eine ganze Zahl sein.")


        # Wahlpflichtbereich
        if 'bereich' in daten and not daten.get('bereich'):
            fehler.append("- Bereich ist für ein Wahlpflichtmodul ein Pflichtfeld.")

        return len(fehler) == 0, fehler


class PruefungsleistungValidator:
    """
    Validator für Prüfungsleistungs-Daten.
    Kapselt alle Geschäftsregeln für die Prüfungsleistungs-Validierung.
    """

    @staticmethod
    def validiere(daten: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validiert und normalisiert Prüfungsleistungs-Daten.
        Setzt Standardwerte, falls diese fehlen (z.B. Versuch).

        :param daten: Dictionary mit Prüfungsleistungs-Daten (wird modifiziert!)
        :return: (ist_gueltig: bool, fehler: List[str])
        """
        fehler = []

        # Note (Pflichtfeld)
        note_str = str(daten.get('note', '')).replace(',', '.')
        if not note_str:
            fehler.append("- Note ist ein Pflichtfeld.")
        else:
            try:
                note = float(note_str)
                if not (1.0 <= note <= 6.0):
                    fehler.append("- Note muss zwischen 1.0 und 6.0 liegen.")
            except ValueError:
                fehler.append("- Note muss eine Zahl sein.")

        # Versuch (Auto-Fill und Validierung)
        if 'versuch' not in daten or not daten.get('versuch'):
            daten['versuch'] = 1  # Standardwert setzen

        try:
            versuch = int(daten['versuch'])
            if versuch not in MOEGLICHE_VERSUCHE:
                fehler.append(f"- Versuch muss einer der folgenden Werte sein: {MOEGLICHE_VERSUCHE}")
        except (ValueError, TypeError):
            fehler.append("- Versuch muss eine ganze Zahl sein.")

        # Punkte (optional)
        punkte_str = str(daten.get('punkte', '')).replace(',', '.')
        if punkte_str:
            try:
                punkte = float(punkte_str)
                if not (0 <= punkte <= 100):
                    fehler.append("- Punkte müssen zwischen 0 und 100 liegen.")
            except ValueError:
                fehler.append("- Punkte müssen eine Zahl sein.")

        # Datum (optional)
        datum_str = daten.get('datum')
        if datum_str:
            try:
                datetime.strptime(datum_str, '%d.%m.%Y')
            except ValueError:
                fehler.append("- Datum muss im Format TT.MM.JJJJ sein.")

        return len(fehler) == 0, fehler
