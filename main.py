import tkinter as tk
from backend.repository.repository import DBManager, DatabaseConnection
from backend.controller import DashboardController
from ui.dashboard import StudienDashboard

DB_DATEI = "database/studium_verwaltung.db"


def main():
    """
    Einstiegspunkt der Anwendung.
    Initialisiert die DB-Verbindung, den DBManager, den Controller und die View.
    """
    db_connection = None
    try:
        # 1. Datenbank-Verbindung initialisieren.
        db_connection = DatabaseConnection(DB_DATEI)
        db_connection.verbinden()

        # 2. DBManager initialisieren (nutzt die Verbindung).
        db_manager = DBManager(db_connection)

        # 3. Controller erstellen.
        controller = DashboardController(db_manager)

        # 4. Hauptfenster (root) für die GUI erstellen.
        root = tk.Tk()

        # 5. Die Haupt-GUI-Klasse initialisieren und Controller übergeben. Man kann da theoretisch direkt Studiendashboard aufrufen
        # ohne es in app zu speichern, aber ich lass es falls man es zum debuggen braucht.
        app = StudienDashboard(root, controller)

        # 6. Die GUI-Event-Schleife starten.
        root.mainloop()

    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")

    finally:
        if db_connection:
            db_connection.schliessen()


if __name__ == "__main__":
    main()