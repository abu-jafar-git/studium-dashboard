from typing import Optional, Dict, Any, Tuple, List, Callable
from backend.repository.repository import DBManager
from backend.validators import StudiengangValidator, ModulValidator, PruefungsleistungValidator

class DashboardController:
    """
    Der Controller verbindet die Benutzeroberfläche (View) mit der Datenbank (Model).
    Er orchestriert den Ablauf, führt die Geschäftslogik aus und stellt Datenintegrität sicher.
    """

    def __init__(self, db_manager: DBManager):
        self.repository = db_manager
        self.view = None

    def set_view(self, view):
        """Setzt die Referenz zur View (Dashboard), um Updates auszulösen."""
        self.view = view
        self._aktualisiere_kpis()


    #Daten-Abruf Lesezugriff
    def lade_studiengang(self):
        """Lädt das Studiengang-Objekt aus der Datenbank."""
        return self.repository.lade_studiengang()

    def lade_modul(self, modul_id: int):
        """Lädt ein einzelnes Modul."""
        return self.repository.lade_modul(modul_id)

    def lade_semester(self, semester_id: int):
        """Lädt ein einzelnes Semester-Objekt (mit seinen Modulen) direkt aus der DB."""
        return self.repository.lade_semester(semester_id)

    def hole_alle_pflichtmodule(self, nur_freie: bool = False):
        module = self.repository.hole_alle_pflichtmodule()
        return [m for m in module if m.ist_frei()] if nur_freie else module

    def hole_alle_wahlpflichtmodule(self, nur_freie: bool = False):
        module = self.repository.hole_alle_wahlpflichtmodule()
        return [m for m in module if m.ist_frei()] if nur_freie else module

    def hole_verfuegbare_wp_bereiche(self) -> List[str]:
        return self.repository.hole_verfuegbare_wp_bereiche()

    def setze_aktives_semester(self, semester_id: int) -> None:
        """Setzt ein Semester als aktiv und steuert die View."""
        semester = self.lade_semester(semester_id)
        erfolg, nachricht = self.repository.setze_aktives_semester(semester_id)
        if erfolg:
            self.view.zeige_erfolgsmeldung(f"Semester {semester.nummer} ist jetzt aktiv.")
            self.view.zeige_semester_detail(semester_id)
        else:
            self.view.zeige_fehlermeldung(nachricht)


    #Aktionen mit Geschäftslogik

    def neues_semester_erstellen(self) -> None:
        """
        Orchestriert das Hinzufügen eines neuen Semesters und steuert die View.
        """
        try:
            # 1. Aktuellen Stand laden
            studiengang = self.repository.lade_studiengang()

            # 2. Geschäftslogik an das Model delegieren
            neues_semester = studiengang.erstelle_neues_semester()

            # 3. Persistieren
            semester_id = self.repository.speichere_semester(neues_semester)
            if not semester_id:
                # Im Fehlerfall die View informieren
                self.view.zeige_fehlermeldung("Fehler beim Speichern des Semesters.")
                return

            # 4. View über Erfolg informieren und zum Neuzeichnen anweisen
            self.view.lade_und_zeichne_dashboard()
            self.view.zeige_erfolgsmeldung(f"Semester {neues_semester.nummer} erfolgreich erstellt.")

        except Exception as e:
            self.view.zeige_fehlermeldung(f"Fehler beim Erstellen des Semesters: {e}")

    def letztes_semester_loeschen(self) -> None:
        """
        Orchestriert das Löschen des letzten Semesters und steuert die View.
        """
        try:
            studiengang = self.repository.lade_studiengang()
            semester_zum_loeschen = studiengang.hole_letztes_semester_zum_loeschen()
            erfolg = self.repository.loesche_semester_by_id(semester_zum_loeschen.id)
            if not erfolg:
                self.view.zeige_fehlermeldung("Fehler beim Löschen des Semesters aus der Datenbank.")
                return

            self.view.lade_und_zeichne_dashboard()
            self.view.zeige_erfolgsmeldung(f"Semester {semester_zum_loeschen.nummer} erfolgreich gelöscht.")

        except ValueError as e:
            self.view.zeige_fehlermeldung(str(e))
        except Exception as e:
            self.view.zeige_fehlermeldung(f"Ein unerwarteter Fehler ist aufgetreten: {e}")

    def modul_loeschen(self, modul_id: int, callback: Optional[Callable] = None) -> None:
        """
        Orchestriert das Löschen eines Moduls und steuert die View.
        """
        try:
            modul = self.repository.lade_modul(modul_id)
            if not modul:
                self.view.zeige_fehlermeldung("Modul nicht gefunden.")
                return

            modul.pruefe_ob_loeschbar()

            self.repository.loesche_modul(modul_id)
            self._aktualisiere_kpis()

            self.view.zeige_erfolgsmeldung(f"Modul '{modul.name}' erfolgreich gelöscht.")

            # UI-Refresh-Logik
            if callback:
                callback()
            elif modul.semester_id:
                self.view.zeige_semester_detail(modul.semester_id)
            else:
                self.view.lade_und_zeichne_dashboard()

        except ValueError as e:
            self.view.zeige_fehlermeldung(str(e))
        except Exception as e:
            self.view.zeige_fehlermeldung(f"Fehler beim Löschen des Moduls: {e}")

    def modul_aus_semester_entfernen(self, modul_id: int) -> None:
        """
        Orchestriert das Entfernen eines Moduls aus einem Semester und steuert die View.
        """
        try:
            modul = self.repository.lade_modul(modul_id)
            if not modul:
                self.view.zeige_fehlermeldung("Modul nicht gefunden.")
                return

            erfolg = self.repository.entferne_modul_aus_semester(modul_id)
            if not erfolg:
                self.view.zeige_fehlermeldung("Fehler beim Entfernen des Moduls.")
                return

            self._aktualisiere_kpis()

            self.view.zeige_semester_detail(modul.semester_id)
            self.view.zeige_erfolgsmeldung(f"Modul '{modul.name}' aus Semester entfernt.")

        except ValueError as e:
            self.view.zeige_fehlermeldung(str(e))
        except Exception as e:
            self.view.zeige_fehlermeldung(f"Fehler: {e}")

    def weise_modul_semester_zu(self, modul_id: int, semester_id: int, callback: Optional[Callable] = None) -> None:
        """Weist ein Modul einem Semester zu."""
        erfolg = self.repository.weise_modul_semester_zu(modul_id, semester_id)
        if erfolg:
            self._aktualisiere_kpis()
            self.view.zeige_erfolgsmeldung("Modul erfolgreich zugewiesen.")
            if callback:
                callback()
        else:
            self.view.zeige_fehlermeldung("Fehler beim Zuweisen des Moduls.")

    def speichere_modul(self, basis_daten: Dict[str, Any], pruef_daten: Optional[Dict[str, Any]], modul_id: Optional[int], callback: Optional[Callable] = None) -> None:
        """
        Speichert ein Modul und steuert die View.
        """
        fehler = []
        modul_gueltig, modul_fehler = ModulValidator.validiere(basis_daten)
        if not modul_gueltig:
            fehler.extend(modul_fehler)

        if pruef_daten:
            pruef_gueltig, pruef_fehler = PruefungsleistungValidator.validiere(pruef_daten)
            if not pruef_gueltig:
                fehler.extend(pruef_fehler)

        if fehler:
            self.view.zeige_fehlermeldung("Folgende Fehler sind aufgetreten:\n" + "\n".join(fehler))
            return

        if modul_id:
            modul = self.repository.lade_modul(modul_id)
            modul.status = basis_daten.get('status')
            loesche_pruefungsleistung = modul.soll_pruefungsleistung_loeschen()
        else:
            loesche_pruefungsleistung = False
        erfolg, nachricht = self.repository.bearbeite_modul_pruefungsleistung(
            basis_daten, pruef_daten, modul_id, loesche_pruefungsleistung=loesche_pruefungsleistung
        )
        if erfolg:
            self._aktualisiere_kpis()
            self.view.zeige_erfolgsmeldung(nachricht)
            if callback:
                callback()
        else:
            self.view.zeige_fehlermeldung(nachricht)

    def speichere_studiengang_details(self, daten: Dict[str, Any], callback: Optional[Callable] = None) -> None:
        """
        Speichert Studiengang-Details und steuert die View.
        """
        gueltig, fehler = StudiengangValidator.validiere(daten)
        if not gueltig:
            self.view.zeige_fehlermeldung("Folgende Fehler sind aufgetreten:\n" + "\n".join(fehler))
            return

        erfolg, nachricht = self.repository.speichere_studiengang_details(daten)
        if erfolg:
            self._aktualisiere_kpis()
            self.view.zeige_erfolgsmeldung(nachricht)
            if callback:
                callback()
        else:
            self.view.zeige_fehlermeldung(nachricht)

    def exportiere_csv(self, dateipfad: str):
        """Führt den CSV-Export durch und informiert die View."""
        try:
            self.repository.csv_exporter.exportiere_daten_als_csv(dateipfad)
            self.view.zeige_erfolgsmeldung("Backup wurde erfolgreich erstellt! 🎉")
        except Exception as e:
            self.view.zeige_fehlermeldung(f"Export fehlgeschlagen: {e}")

    def testdaten_laden(self) -> None:
        """Setzt die Datenbank auf Testdaten zurück und steuert die View."""
        try:
            self.repository.initialisiere_datenbank_neu(modus="test")
            self._aktualisiere_kpis()  # KPI-Werte nach dem Laden neu berechnen und speichern
            self.view.lade_und_zeichne_dashboard()
            self.view.zeige_erfolgsmeldung("Testdaten wurden erfolgreich geladen!")
        except Exception as e:
            self.view.zeige_fehlermeldung(f"Vorgang fehlgeschlagen: {e}")

    def datenbank_leeren(self) -> None:
        """Leert die Datenbank komplett und steuert die View."""
        try:
            self.repository.initialisiere_datenbank_neu(modus="leer")
            self._aktualisiere_kpis()  # Sicherstellen, dass auch hier alles sauber ist
            self.view.lade_und_zeichne_dashboard()
            self.view.zeige_erfolgsmeldung("Datenbank wurde erfolgreich geleert!")
        except Exception as e:
            self.view.zeige_fehlermeldung(f"Vorgang fehlgeschlagen: {e}")


    #Private Hilfsmethode für Datenintegrität
    def _aktualisiere_kpis(self):
        """
        Private Hilfsmethode für Datenintegrität.
        Stellt sicher, dass KPIs nach Änderungen aktualisiert werden.
        Diese Methode koordiniert die Berechnung (nutzt Models) und Persistierung (nutzt Repository).
        """
        # 1. Studiengang laden
        studiengang = self.repository.lade_studiengang()

        # 2. Studiengang-KPIs neu berechnen (Domänenlogik im Model)
        studiengang.aktualisiere_kpis()

        # 3. Semester-KPIs neu berechnen (Domänenlogik im Model)
        for semester in studiengang.semester_liste:
            semester.aktualisiere_kpis()

        # 4. Zurückschreiben
        self.repository.aktualisiere_kpis(studiengang)
