# Studien-Dashboard

Ein Dashboard für das eigene Studium als Desktop-Anwendung in Python.
Es zeigt auf einen Blick Notenschnitt, ECTS-Fortschritt, Zeitverlauf und abgeschlossene Module
und verwaltet Semester, Module und Prüfungsleistungen.

Projekt im Kurs **Objektorientierte und funktionale Programmierung mit Python (DLBDSOOFPP01_D)**
an der IU Internationale Hochschule.

## Voraussetzungen

- Python 3.10 oder neuer ([python.org/downloads](https://www.python.org/downloads/))
- Bei der Installation unter Windows „Add python.exe to PATH“ anhaken
- Keine zusätzlichen Pakete nötig: Tkinter und SQLite sind in Python enthalten

Getestet unter Windows 11.

## Installation und Start

1. Auf dieser Seite auf **Code → Download ZIP** klicken und die ZIP-Datei entpacken
   (oder `git clone https://github.com/abu-jafar-git/studium-dashboard.git`).
2. Im Projektordner (dort, wo `main.py` liegt) die Eingabeaufforderung öffnen,
   z. B. `cmd` in die Adressleiste des Explorers eingeben.
3. Programm starten:

   ```
   python main.py
   ```

   Falls der Befehl nicht gefunden wird: `py main.py`

Das Programm muss aus dem Projektordner gestartet werden, da der Pfad zur Datenbank relativ angegeben ist.

## Erster Start

- Die Datenbank wird beim ersten Start automatisch im Ordner `database/` angelegt.
- **Testdaten laden** lädt einen Beispiel-Studiengang mit Semestern und Modulen.
- **DB Leeren** setzt auf einen leeren Studiengang zurück (vorher wird eine Sicherung in `database/Backup/` erstellt).
- **Backup (CSV)** exportiert alle Module als CSV-Datei.

## Projektstruktur

```
main.py                         Startpunkt
ui/
  dashboard.py                  View: StudienDashboard, ScrollableFrame
backend/
  controller.py                 Controller
  models/                       Domäne: Studiengang, Semester, Modul, WahlpflichtModul, Pruefungsleistung
  repository/
    repository.py               Infrastruktur: DBManager, DatabaseConnection, CsvExporter
    datenbank_setup/            Aufbau der Datenbank (Schema, leere DB, Testdaten)
  querschnitt/
    constants.py                Konstanten (Farben, Status, Fachregeln)
    validators.py               Validatoren für Benutzereingaben
```

## Architektur

Das Programm ist in vier Schichten aufgeteilt:

- **View** zeigt nur an und gibt jede Aktion an den Controller weiter.
- **Controller** lässt Eingaben prüfen, ruft die Fachlogik auf und lässt Änderungen speichern.
- **Domäne** enthält die Fachlogik, z. B. die Berechnung von Notenschnitt und ECTS.
- **Infrastruktur** enthält nur den Datenbankzugriff (SQLite).

Nach jeder Änderung werden alle Kennzahlen neu berechnet und in der Datenbank gespeichert,
sodass die Oberfläche nur fertige Werte ausliest.
