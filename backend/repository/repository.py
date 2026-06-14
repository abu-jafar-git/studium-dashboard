import sqlite3
import os
import csv
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime, date
from backend.models.studiengang import Studiengang
from backend.models.semester import Semester
from backend.models.modul import Modul, WahlpflichtModul
from backend.models.pruefungsleistung import Pruefungsleistung
from database.create_db import initialisiere_datenbank


class DatabaseConnection:
    """
    Verwaltet die physische Verbindung zur SQLite-Datenbank.
    """
    def __init__(self, db_pfad: str):
        self.db_pfad = db_pfad
        self.verbindung: Optional[sqlite3.Connection] = None

    def verbinden(self):
        """Stellt die Verbindung her oder initialisiert die DB neu, falls nicht vorhanden."""
        if not os.path.exists(self.db_pfad):
            print(f"[INFO] Datenbank '{self.db_pfad}' nicht gefunden. Initialisiere neu...")
            try:
                initialisiere_datenbank(self.db_pfad, modus="leer")
            except Exception as e:
                print(f"[FEHLER] Fehler bei Initialisierung: {e}")
                return

        try:
            self.verbindung = sqlite3.connect(self.db_pfad)
            self.verbindung.row_factory = sqlite3.Row
            self.verbindung.execute("PRAGMA foreign_keys = ON")
        except sqlite3.Error as e:
            print(f"[FEHLER] Fehler beim Verbinden mit der Datenbank: {e}")
            self.verbindung = None

    def schliessen(self):
        """Schließt die Verbindung."""
        if self.verbindung:
            self.verbindung.close()
            self.verbindung = None

    def get_connection(self) -> Optional[sqlite3.Connection]:
        """Gibt das Verbindungsobjekt zurück."""
        return self.verbindung


class CsvExporter:
    """
    Verantwortlich für den Export von Daten in das CSV-Format.
    """
    def __init__(self, db_connection: DatabaseConnection):
        self.db_connection = db_connection

    def exportiere_daten_als_csv(self, dateipfad: str):
        """
        Exportiert alle relevanten Moduldaten in eine CSV-Datei.
        """
        conn = self.db_connection.get_connection()
        if not conn:
            self.db_connection.verbinden()
            conn = self.db_connection.get_connection()

        cursor = conn.cursor()
        query = """
            SELECT m.id, s.nummer as semester, m.name, m.code, m.ects, m.status,
                   p.note, p.pruefungsart, p.versuch, p.datum, p.punkte, w.bereich
            FROM modul m
            LEFT JOIN semester s ON m.semester_id = s.id
            LEFT JOIN pruefungsleistung p ON m.id = p.modul_id
            LEFT JOIN wahlpflicht_modul w ON m.id = w.modul_id
        """
        cursor.execute(query)
        daten = cursor.fetchall()

        with open(dateipfad, mode='w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(["ID", "Semester", "Modulname", "Code", "ECTS", "Status",
                             "Note", "Prüfungsart", "Versuch", "Datum", "Punkte", "Bereich"])

            for row in daten:
                row_list = list(row)
                # Excel-Hack: Note als String formatieren, damit Excel nicht 1.0 zu 1 macht
                if row_list[6]:
                    row_list[6] = f'="{row_list[6]}"'
                writer.writerow(row_list)


class DBManager:
    """
    Verwaltet alle Datenbankoperationen.
    Nutzt DatabaseConnection für den Zugriff.
    """

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialisiert den DBManager.
        :param db_connection: Eine Instanz von DatabaseConnection.
        """
        self.db_connection = db_connection
        # Initialisiert den CSV-Exporter
        self.csv_exporter = CsvExporter(db_connection)

    #Lesezugriff

    def lade_studiengang(self) -> Studiengang:
        """
        Lädt den gesamten Objektgraphen aus der Datenbank.
        Diese Methode gibt IMMER ein Studiengang-Objekt zurück.
        """
        conn = self.db_connection.get_connection()
        if not conn:
            print("[INFO] Verbindung zur Datenbank nicht hergestellt. Gebe leeres Objekt zurück.")
            return Studiengang()

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM studiengang WHERE id = 1")
        stg_row = cursor.fetchone()

        if not stg_row:
            return Studiengang()

        beginn_datum = self._parse_datum(stg_row['beginn'])

        studiengang_obj = Studiengang(
            id=stg_row['id'],
            name=stg_row['name'],
            ziel_notenschnitt=stg_row['ziel_notenschnitt'],
            ziel_ects=stg_row['ziel_ects'],
            beginn=beginn_datum,
            ziel_abschlussdauer=stg_row['ziel_abschlussdauer'],
            aktuelle_notenschnitt=stg_row['aktuelle_notenschnitt'],
            aktuelle_ects=stg_row['aktuelle_ects'],
            aktuelle_zeit_in_monat=stg_row['aktuelle_zeit_in_monat'],
            gesamte_module=stg_row['gesamte_module'],
            abgeschlossene_module=stg_row['abgeschlossene_module']
        )

        semester_map: Dict[int, Semester] = {}
        cursor.execute("SELECT * FROM semester ORDER BY nummer")
        for sem_row in cursor.fetchall():
            semester_obj = Semester(
                id=sem_row['id'],
                studiengang_id=sem_row['studiengang_id'],
                nummer=sem_row['nummer'],
                ist_aktiv=(sem_row['status'] == 'Aktiv'),
                notenschnitt_semester=sem_row['notenschnitt_semester'],
                aktuelle_ects_semester=sem_row['aktuelle_ects_semester']
            )
            studiengang_obj.verknuepfe_semester(semester_obj)
            semester_map[semester_obj.id] = semester_obj

        sql = """
            SELECT
                m.id as modul_id, m.semester_id, m.name, m.code, m.ects, m.status,
                w.bereich,
                p.id as leistung_id, p.punkte, p.note, p.datum, p.versuch, p.pruefungsart
            FROM modul m
            LEFT JOIN wahlpflicht_modul w ON m.id = w.modul_id
            LEFT JOIN pruefungsleistung p ON m.id = p.modul_id
            ORDER BY m.id
        """
        cursor.execute(sql)

        module_map: Dict[int, Modul] = {}
        for row in cursor.fetchall():
            modul_id = row['modul_id']

            if modul_id not in module_map:
                modul_obj = self._row_zu_modul(row)
                module_map[modul_id] = modul_obj
                if modul_obj.semester_id and modul_obj.semester_id in semester_map:
                    semester_map[modul_obj.semester_id].module.append(modul_obj)

            if row['leistung_id']:
                leistung_obj = Pruefungsleistung(
                    id=row['leistung_id'], modul_id=modul_id, punkte=row['punkte'],
                    note=row['note'], datum=self._parse_datum(row['datum']),
                    versuch=row['versuch'], pruefungsart=row['pruefungsart']
                )
                module_map[modul_id].setze_leistung(leistung_obj)

        return studiengang_obj

    def lade_modul(self, modul_id: int) -> Optional[Modul]:
        """
        Lädt ein einzelnes Modul mit allen Details (inkl. Prüfungsleistung und WP-Bereich)
        frisch aus der Datenbank.
        """
        conn = self.db_connection.get_connection()
        if not conn:
            self.db_connection.verbinden()
            conn = self.db_connection.get_connection()
        cursor = conn.cursor()

        sql = """
            SELECT
                m.id as modul_id, m.semester_id, m.name, m.code, m.ects, m.status,
                w.bereich,
                p.id as leistung_id, p.punkte, p.note, p.datum, p.versuch, p.pruefungsart
            FROM modul m
            LEFT JOIN wahlpflicht_modul w ON m.id = w.modul_id
            LEFT JOIN pruefungsleistung p ON m.id = p.modul_id
            WHERE m.id = ?
        """
        cursor.execute(sql, (modul_id,))
        row = cursor.fetchone()

        if not row:
            return None

        modul_obj = self._row_zu_modul(row)

        if row['leistung_id']:
            leistung_obj = Pruefungsleistung(
                id=row['leistung_id'], modul_id=row['modul_id'], punkte=row['punkte'],
                note=row['note'], datum=self._parse_datum(row['datum']),
                versuch=row['versuch'], pruefungsart=row['pruefungsart']
            )
            modul_obj.setze_leistung(leistung_obj)

        return modul_obj

    def lade_semester(self, semester_id: int) -> Optional[Semester]:
        """
        Lädt ein einzelnes Semester mit allen zugehörigen Modulen und Prüfungsleistungen
        direkt aus der DB.
        """
        conn = self.db_connection.get_connection()
        if not conn:
            return None
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM semester WHERE id = ?", (semester_id,))
        sem_row = cursor.fetchone()
        if not sem_row:
            return None

        semester_obj = Semester(
            id=sem_row['id'],
            studiengang_id=sem_row['studiengang_id'],
            nummer=sem_row['nummer'],
            ist_aktiv=(sem_row['status'] == 'Aktiv'),
            notenschnitt_semester=sem_row['notenschnitt_semester'],
            aktuelle_ects_semester=sem_row['aktuelle_ects_semester']
        )

        sql = """
            SELECT
                m.id as modul_id, m.semester_id, m.name, m.code, m.ects, m.status,
                w.bereich,
                p.id as leistung_id, p.punkte, p.note, p.datum, p.versuch, p.pruefungsart
            FROM modul m
            LEFT JOIN wahlpflicht_modul w ON m.id = w.modul_id
            LEFT JOIN pruefungsleistung p ON m.id = p.modul_id
            WHERE m.semester_id = ?
            ORDER BY m.id
        """
        cursor.execute(sql, (semester_id,))
        for row in cursor.fetchall():
            modul_obj = self._row_zu_modul(row)
            if row['leistung_id']:
                leistung_obj = Pruefungsleistung(
                    id=row['leistung_id'], modul_id=row['modul_id'], punkte=row['punkte'],
                    note=row['note'], datum=self._parse_datum(row['datum']),
                    versuch=row['versuch'], pruefungsart=row['pruefungsart']
                )
                modul_obj.setze_leistung(leistung_obj)
            semester_obj.module.append(modul_obj)

        return semester_obj

    def hole_alle_pflichtmodule(self) -> List[Modul]:
        """
        Liefert alle Pflichtmodule (nicht Wahlpflicht), sortiert nach Semester und ID.
        """
        conn = self.db_connection.get_connection()
        if not conn:
            self.db_connection.verbinden()
            conn = self.db_connection.get_connection()
        cursor = conn.cursor()
        query = """
            SELECT m.id, m.name, m.code, m.ects, m.status, m.semester_id, s.nummer as semester_nummer
            FROM modul m
            LEFT JOIN semester s ON m.semester_id = s.id
            WHERE m.id NOT IN (SELECT modul_id FROM wahlpflicht_modul)
            ORDER BY s.nummer, m.id
        """
        cursor.execute(query)
        return [Modul(id=r['id'], name=r['name'], code=r['code'], ects=r['ects'],
                      status=r['status'], semester_id=r['semester_id'],
                      semester_nummer=r['semester_nummer']) for r in cursor.fetchall()]

    def hole_alle_wahlpflichtmodule(self) -> List[WahlpflichtModul]:
        """
        Liefert alle Wahlpflichtmodule, sortiert nach Bereich, Semester und ID.
        """
        conn = self.db_connection.get_connection()
        if not conn:
            self.db_connection.verbinden()
            conn = self.db_connection.get_connection()
        cursor = conn.cursor()
        query = """
            SELECT m.id, m.name, m.code, m.ects, m.status, m.semester_id, w.bereich, s.nummer as semester_nummer
            FROM modul m
            JOIN wahlpflicht_modul w ON m.id = w.modul_id
            LEFT JOIN semester s ON m.semester_id = s.id
            ORDER BY w.bereich, s.nummer, m.id
        """
        cursor.execute(query)
        return [WahlpflichtModul(id=r['id'], name=r['name'], code=r['code'], ects=r['ects'],
                                 status=r['status'], semester_id=r['semester_id'],
                                 wahlpflichtbereich=r['bereich'], semester_nummer=r['semester_nummer']) for r in cursor.fetchall()]

    def hole_verfuegbare_wp_bereiche(self) -> List[str]:
        """
        Liefert eine Liste aller bereits verwendeten Wahlpflichtbereiche (z.B. ['A', 'B', 'C']).
        """
        conn = self.db_connection.get_connection()
        if not conn:
            self.db_connection.verbinden()
            conn = self.db_connection.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT bereich FROM wahlpflicht_modul WHERE bereich IS NOT NULL ORDER BY bereich")
        return [row[0] for row in cursor.fetchall()]


    #Schreibzugriff
    def aktualisiere_kpis(self, studiengang):
        """
        Schreibt die bereits berechneten KPIs in die Datenbank.
        Diese Methode macht NUR SQL - keine Berechnungen!
        """
        conn = self.db_connection.get_connection()
        if not conn:
            return

        try:
            stg_sql = """
                UPDATE studiengang SET
                    aktuelle_notenschnitt = ?, aktuelle_ects = ?, aktuelle_zeit_in_monat = ?,
                    gesamte_module = ?, abgeschlossene_module = ?
                WHERE id = 1
            """
            conn.execute(stg_sql, (
                studiengang.aktuelle_notenschnitt,
                studiengang.aktuelle_ects,
                studiengang.aktuelle_zeit_in_monat,
                studiengang.gesamte_module,
                studiengang.abgeschlossene_module
            ))

            sem_sql = "UPDATE semester SET notenschnitt_semester = ?, aktuelle_ects_semester = ? WHERE id = ?"
            semester_updates = []
            for semester in studiengang.semester_liste:
                semester_updates.append((
                    semester.notenschnitt_semester,
                    semester.aktuelle_ects_semester,
                    semester.id
                ))

            conn.executemany(sem_sql, semester_updates)
            conn.commit()

        except sqlite3.Error as e:
            conn.rollback()
            print(f"[FEHLER] Fehler beim Schreiben der KPI-Werte: {e}")

    def speichere_semester(self, semester) -> Optional[int]:
        """
        Speichert ein neues Semester in der Datenbank.
        """
        conn = self.db_connection.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO semester (studiengang_id, nummer, status) VALUES (?, ?, ?)",
                (semester.studiengang_id, semester.nummer, 'Nicht aktiv')
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[FEHLER] Fehler beim Speichern des Semesters: {e}")
            return None

    def loesche_modul(self, modul_id: int):
        """
        Löscht ein Modul aus der Datenbank.
        Macht NUR SQL - keine Validierung, keine KPI-Aktualisierung!
        """
        conn = self.db_connection.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM modul WHERE id=?", (modul_id,))
            conn.commit()
        except sqlite3.Error as e:
            print(f"[FEHLER] Fehler beim Löschen des Moduls: {e}")
            raise e

    def loesche_semester_by_id(self, semester_id: int) -> bool:
        """
        Löscht ein spezifisches Semester anhand seiner ID.
        """
        conn = self.db_connection.get_connection()
        try:
            conn.execute("DELETE FROM semester WHERE id = ?", (semester_id,))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"[FEHLER] Fehler beim Löschen von Semester {semester_id}: {e}")
            return False

    def speichere_studiengang_details(self, daten: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Speichert die Kerndaten des Studiengangs (nur SQL, keine Validierung).
        """
        conn = self.db_connection.get_connection()
        ziel_schnitt = float(str(daten.get('ziel_schnitt', '0')).replace(',', '.'))
        ziel_ects = int(daten.get('ziel_ects', 0))
        ziel_dauer = int(daten.get('ziel_dauer', 0))
        beginn_str = daten.get('beginn')
        beginn_db = datetime.strptime(beginn_str, '%d.%m.%Y').strftime('%Y-%m-%d') if beginn_str else None

        try:
            sql = "UPDATE studiengang SET name = ?, ziel_notenschnitt = ?, ziel_ects = ?, ziel_abschlussdauer = ?, beginn = ? WHERE id = 1"
            conn.execute(sql, (daten.get('name'), ziel_schnitt, ziel_ects, ziel_dauer, beginn_db))
            conn.commit()
            return True, "Studiengang-Details erfolgreich gespeichert."
        except sqlite3.Error as e:
            return False, f"Datenbankfehler beim Speichern: {e}"

    def bearbeite_modul_pruefungsleistung(self, modul_daten: Dict[str, Any], pruefungs_daten: Optional[Dict[str, Any]], modul_id: Optional[int] = None, loesche_pruefungsleistung: bool = False) -> Tuple[bool, str]:
        """
        Speichert Modul- und Prüfungsdaten in einer Transaktion (nur SQL, keine Validierung).
        """
        conn = self.db_connection.get_connection()

        try:
            erfolg, msg = self._speichere_modul(modul_daten, modul_id, commit=False)
            if not erfolg:
                conn.rollback()
                return False, msg

            if not modul_id:
                modul_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

            if loesche_pruefungsleistung:
                conn.execute("DELETE FROM pruefungsleistung WHERE modul_id = ?", (modul_id,))
            elif pruefungs_daten:
                erfolg, msg = self._speichere_pruefungsleistung(pruefungs_daten, modul_id, commit=False)
                if not erfolg:
                    conn.rollback()
                    return False, msg

            conn.commit()
            return True, "Erfolgreich gespeichert."

        except sqlite3.Error as e:
            conn.rollback()
            return False, f"Datenbankfehler: {e}"

    def weise_modul_semester_zu(self, modul_id: int, semester_id: int) -> bool:
        """
        Weist einem Modul ein Semester zu (nur SQL, keine Validierung).
        """
        conn = self.db_connection.get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE modul SET semester_id = ? WHERE id = ?", (semester_id, modul_id))
            conn.commit()
            return True
        except sqlite3.Error:
            return False

    def entferne_modul_aus_semester(self, modul_id: int) -> bool:
        """
        Entkoppelt ein Modul von seinem Semester (nur SQL, keine Validierung).
        """
        conn = self.db_connection.get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE modul SET semester_id = NULL WHERE id = ?", (modul_id,))
            conn.commit()
            return True
        except sqlite3.Error:
            return False


    #Verwaltung
    def initialisiere_datenbank_neu(self, modus: str):
        """
        Startet den kompletten Neuaufbau der Datenbank.
        """
        self.db_connection.schliessen()
        try:
            initialisiere_datenbank(self.db_connection.db_pfad, modus)
        except Exception as e:
            print(f"[FEHLER] Schwerwiegender Fehler beim Neuaufbau der Datenbank: {e}")
            raise e
        self.db_connection.verbinden()

    def setze_aktives_semester(self, semester_id: int) -> Tuple[bool, str]:
        """
        Setzt ein bestimmtes Semester als 'Aktiv' (nur SQL, keine Validierung).
        """
        conn = self.db_connection.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE semester SET status = 'Nicht aktiv' WHERE status = 'Aktiv'")
            cursor.execute("UPDATE semester SET status = 'Aktiv' WHERE id = ?", (semester_id,))
            conn.commit()
            return True, "Semester erfolgreich auf aktiv gesetzt."
        except sqlite3.Error as e:
            return False, f"Datenbankfehler: {e}"


    #Private Hilfsmethoden
    def _row_zu_modul(self, row) -> Modul:
        """Baut ein Modul- oder WahlpflichtModul-Objekt aus einer DB-Row."""
        if row['bereich']:
            return WahlpflichtModul(
                name=row['name'], id=row['modul_id'], semester_id=row['semester_id'],
                code=row['code'], ects=row['ects'], status=row['status'],
                wahlpflichtbereich=row['bereich']
            )
        return Modul(
            name=row['name'], id=row['modul_id'], semester_id=row['semester_id'],
            code=row['code'], ects=row['ects'], status=row['status']
        )

    def _speichere_modul(self, daten: Dict[str, Any], modul_id: Optional[int] = None, commit: bool = True) -> Tuple[bool, str]:
        """
        Speichert die Kerndaten eines Moduls (nur SQL, keine Validierung).
        """
        conn = self.db_connection.get_connection()
        name = daten.get('name')
        status = daten.get('status')
        ects = int(daten.get('ects', 0))

        cursor = conn.cursor()
        try:
            if modul_id:
                cursor.execute("UPDATE modul SET name=?, code=?, ects=?, status=? WHERE id=?",
                               (name, daten.get('code'), ects, status, modul_id))
            else:
                semester_id = daten.get('semester_id')
                cursor.execute("INSERT INTO modul (name, code, ects, status, semester_id) VALUES (?, ?, ?, ?, ?)",
                               (name, daten.get('code'), ects, status, semester_id))
                modul_id = cursor.lastrowid

            bereich = daten.get('bereich')
            if bereich:
                cursor.execute("SELECT modul_id FROM wahlpflicht_modul WHERE modul_id=?", (modul_id,))
                if cursor.fetchone():
                    cursor.execute("UPDATE wahlpflicht_modul SET bereich=? WHERE modul_id=?", (bereich, modul_id))
                else:
                    cursor.execute("INSERT INTO wahlpflicht_modul (modul_id, bereich) VALUES (?, ?)", (modul_id, bereich))

            if commit:
                conn.commit()
            return True, "Modul-Details erfolgreich gespeichert."
        except sqlite3.Error as e:
            if commit:
                conn.rollback()
            return False, f"Datenbankfehler: {e}"

    @staticmethod
    def _parse_datum(datum_str) -> Optional[date]:
        """
        Parst ein Datum aus ISO-Format ('%Y-%m-%d') oder deutschem Format ('%d.%m.%Y').
        """
        if not datum_str:
            return None
        try:
            return datetime.strptime(datum_str, '%Y-%m-%d').date()
        except ValueError:
            try:
                return datetime.strptime(datum_str, '%d.%m.%Y').date()
            except ValueError:
                print(f"[INFO] Warnung: Unbekanntes Datumsformat: {datum_str}")
                return None

    def _speichere_pruefungsleistung(self, daten: Dict[str, Any], modul_id: int, commit: bool = True) -> Tuple[bool, str]:
        """
        Erstellt oder aktualisiert die Prüfungsleistung (nur SQL, keine Validierung).
        """
        conn = self.db_connection.get_connection()
        note_str = str(daten.get('note', '')).replace(',', '.')
        note = float(note_str) if note_str else None
        punkte_str = str(daten.get('punkte', '')).replace(',', '.')
        punkte = float(punkte_str) if punkte_str else None
        versuch = int(daten.get('versuch'))
        datum_str = daten.get('datum')
        datum_db = datetime.strptime(datum_str, '%d.%m.%Y').strftime('%Y-%m-%d') if datum_str else None

        cursor = conn.cursor()
        try:
            art = daten.get('pruefungsart')
            if not art:
                art = None

            cursor.execute("SELECT id FROM pruefungsleistung WHERE modul_id=?", (modul_id,))
            if cursor.fetchone():
                cursor.execute("UPDATE pruefungsleistung SET punkte=?, note=?, datum=?, versuch=?, pruefungsart=? WHERE modul_id=?",
                               (punkte, note, datum_db, versuch, art, modul_id))
            else:
                cursor.execute("INSERT INTO pruefungsleistung (modul_id, punkte, note, datum, versuch, pruefungsart) VALUES (?, ?, ?, ?, ?, ?)",
                               (modul_id, punkte, note, datum_db, versuch, art))

            if commit:
                conn.commit()
            return True, "Prüfungsleistung erfolgreich gespeichert."
        except sqlite3.Error as e:
            if commit:
                conn.rollback()
            return False, f"Datenbankfehler: {e}"
