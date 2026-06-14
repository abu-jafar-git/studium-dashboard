import sqlite3
import os
import shutil
from datetime import datetime

# Importiert die "Musiker"-Funktionen aus den Seeder-Dateien.
from backend.repository.db_seeder_leere import fuelle_datenbank as fuelle_leere_db
from backend.repository.db_seeder_test_daten import fuelle_datenbank as fuelle_test_db


def erstelle_schema(cursor: sqlite3.Cursor):
    """
    Definiert und erstellt die gesamte Datenbankstruktur (Tabellen, Indizes).
    Dies ist der "Single Source of Truth" für das Datenbankschema.

    :param cursor: Ein aktiver sqlite3-Cursor, um die Befehle auszuführen.
    """
    # Das SQL-Skript enthält alle CREATE-Befehle.
    # Es wird hier zentral verwaltet.
    sql_script = """
        PRAGMA foreign_keys = ON;

        CREATE TABLE `studiengang` (
          `id` INTEGER PRIMARY KEY AUTOINCREMENT,
          `name` TEXT NOT NULL,
          `beginn` DATE DEFAULT NULL,
          `ziel_notenschnitt` REAL DEFAULT NULL,
          `aktuelle_notenschnitt` REAL DEFAULT 0.00,
          `ziel_ects` INTEGER DEFAULT NULL,
          `aktuelle_ects` INTEGER DEFAULT 0,
          `ziel_abschlussdauer` INTEGER DEFAULT NULL,
          `aktuelle_zeit_in_monat` INTEGER DEFAULT 0,
          `gesamte_module` INTEGER DEFAULT NULL,
          `abgeschlossene_module` INTEGER DEFAULT 0
        );

        CREATE TABLE `semester` (
          `id` INTEGER PRIMARY KEY AUTOINCREMENT,
          `studiengang_id` INTEGER,
          `nummer` INTEGER NOT NULL,
          `status` TEXT DEFAULT 'Nicht aktiv',
          `notenschnitt_semester` REAL DEFAULT NULL,
          `aktuelle_ects_semester` INTEGER DEFAULT 0,
          FOREIGN KEY (`studiengang_id`) REFERENCES `studiengang` (`id`) ON DELETE CASCADE
        );

        CREATE TABLE `modul` (
          `id` INTEGER PRIMARY KEY AUTOINCREMENT,
          `semester_id` INTEGER DEFAULT NULL,
          `name` TEXT NOT NULL,
          `code` TEXT DEFAULT NULL,
          `ects` INTEGER DEFAULT 5,
          `status` TEXT DEFAULT 'Geplant' CHECK(status IN ('Bestanden','Nicht bestanden','In Arbeit','Geplant')),
          FOREIGN KEY (`semester_id`) REFERENCES `semester` (`id`) ON DELETE SET NULL
        );

        CREATE TABLE `pruefungsleistung` (
          `id` INTEGER PRIMARY KEY AUTOINCREMENT,
          `modul_id` INTEGER UNIQUE,
          `punkte` REAL DEFAULT NULL,
          `note` REAL DEFAULT NULL CHECK(note >= 1.0 AND note <= 6.0),
          `datum` DATE DEFAULT NULL,
          `versuch` INTEGER DEFAULT 1 CHECK(versuch IN (1, 2, 3)),
          `pruefungsart` TEXT DEFAULT NULL CHECK(pruefungsart IN ('Klausur', 'Hausarbeit', 'Workbook', 'Projektbericht', 'Fallstudie', 'Portfolio', 'Bachelorarbeit', 'Kolloquium') OR pruefungsart IS NULL),
          FOREIGN KEY (`modul_id`) REFERENCES `modul` (`id`) ON DELETE CASCADE
        );

        CREATE TABLE `wahlpflicht_modul` (
          `modul_id` INTEGER PRIMARY KEY,
          `bereich` TEXT DEFAULT NULL,
          FOREIGN KEY (`modul_id`) REFERENCES `modul` (`id`) ON DELETE CASCADE
        );

        CREATE INDEX semester_studiengang_id ON semester(studiengang_id);
        CREATE INDEX modul_semester_id ON modul(semester_id);
        CREATE INDEX pruefungsleistung_modul_id ON pruefungsleistung(modul_id);
    """
    # Führt das gesamte Skript auf einmal aus.
    cursor.executescript(sql_script)


def initialisiere_datenbank(db_pfad: str, modus: str, backup_ordner: str = "database/Backup"):
    """
    Steuert den gesamten Prozess der Datenbank-Initialisierung.
    Erstellt ein Backup, löscht die alte DB und baut sie je nach Modus neu auf.

    :param db_pfad: Der Pfad zur Datenbankdatei (z.B. "studium_verwaltung.db").
    :param modus: Der Modus für die Befüllung ("leer" oder "test").
    :param backup_ordner: Der Name des Ordners für die Backups.
    """

    # 1. Backup der alten Datenbank erstellen, falls sie existiert.
    if os.path.exists(db_pfad):
        if not os.path.exists(backup_ordner):
            os.makedirs(backup_ordner)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_pfad = os.path.join(backup_ordner, f"{modus}_backup_{timestamp}.db")

        try:
            shutil.copy2(db_pfad, backup_pfad)
        except Exception as e:
            print(f"[FEHLER] Fehler beim Erstellen des Backups: {e}")
            # Hier brechen wir nicht ab, da das Backup optional ist.

    # 2. Alte Datenbank löschen, um einen sauberen Start zu gewährleisten.
    if os.path.exists(db_pfad):
        try:
            os.remove(db_pfad)
        except Exception as e:
            print(f"[FEHLER] Fehler beim Löschen der alten Datenbank: {e}")
            raise e

    # 3. Neue Datenbankverbindung herstellen (erstellt die leere Datei) und Schema anlegen.
    try:
        conn = sqlite3.connect(db_pfad)
        cursor = conn.cursor()

        # 4. Tabellenstruktur über die zentrale Schema-Funktion erstellen.
        erstelle_schema(cursor)

        # Änderungen am Schema committen, bevor die Seeder aufgerufen werden.
        conn.commit()

        # 5. Datenbank je nach Modus mit Daten befüllen.
        if modus == "test":
            # Ruft den "Musiker" für die Test-Daten auf.
            fuelle_test_db(conn)
        else:
            # Ruft den "Musiker" für die leere Datenbank auf.
            fuelle_leere_db(conn)

    except sqlite3.Error as e:
        raise e  # Auch DB-Fehler weiterwerfen
    finally:
        # 6. Verbindung sauber schließen.
        if 'conn' in locals() and conn:
            conn.close()