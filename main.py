import tkinter as tk
from backend.repository.repository import DBManager, DatabaseConnection
from backend.controller import Controller
from ui.dashboard import StudienDashboard

DB_DATEI = "database/studium_verwaltung.db"


def main():
    """
    Einstiegspunkt der Anwendung.
    Initialisiert die DB-Verbindung, den DBManager, den Controller und die View.
    """
    db_connection = None
    try:
        # Datenbank-Verbindung aufbauen
        db_connection = DatabaseConnection(DB_DATEI)
        db_connection.verbinden()

        # DBManager erstellen (nutzt die Verbindung)
        db_manager = DBManager(db_connection)

        # Controller erstellen
        controller = Controller(db_manager)

        # Hauptfenster (root) für die GUI erstellen
        root = tk.Tk()

        # Dashboard erstellen und den Controller übergeben
        # app wird nicht weiter genutzt, ist aber beim Debuggen praktisch
        app = StudienDashboard(root, controller)

        # GUI-Event-Schleife starten
        root.mainloop()

    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")

    finally:
        if db_connection:
            db_connection.schliessen()


if __name__ == "__main__":
    main()