import sqlite3

def fuelle_datenbank(conn: sqlite3.Connection):
    """
    Füllt die Datenbank mit einem leeren Studiengang.
    Diese Funktion erwartet eine bereits geöffnete Datenbankverbindung.
    """
    cursor = conn.cursor()

    # Leeren Studiengang anlegen
    cursor.execute("""
        INSERT INTO studiengang (name)
        VALUES ('Mein Studiengang')
    """)

    conn.commit()
