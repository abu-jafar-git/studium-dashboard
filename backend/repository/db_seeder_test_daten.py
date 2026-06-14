import sqlite3

def fuelle_datenbank(conn: sqlite3.Connection):
    """
    Füllt die Datenbank mit den 61 Test-Modulen.
    Diese Funktion erwartet eine bereits geöffnete Datenbankverbindung.
    """
    cursor = conn.cursor()

    # 1. Studiengang EINMALIG anlegen
    cursor.execute("""
            INSERT INTO studiengang
            (id, name, ziel_notenschnitt, ziel_ects, ziel_abschlussdauer, beginn, gesamte_module)
            VALUES (1, 'B.Sc. Cyber Security', 2.0, 180, 36, '01.09.2025', 36)
        """)

    # 2. Semester 1-6 anlegen (Semester 3 ist aktiv)
    for i in range(1, 7):
        status = 'Aktiv' if i == 3 else 'Nicht aktiv'
        cursor.execute("INSERT INTO semester (id, studiengang_id, nummer, status) VALUES (?, 1, ?, ?)", (i, i, status))

    # 3. Module, Noten & Wahlpflicht-Zuweisung
    # Daten-Format: (ID, Semester_ID, Name, Code, ECTS, Status, Note, Art, Versuch, Datum, Punkte, Bereich)
    test_daten = [
        (11, 1, 'Betriebssysteme, Rechnernetze und verteilte Systeme', 'DLBIBRVS01', 5, 'Bestanden', 1.7, 'Klausur',
         '1', '13.11.2025', 86.6, None),
        (12, 1, 'Einführung in Datenschutz und IT-Sicherheit', 'DLBISIC01', 5, 'Nicht bestanden', 5.0, 'Klausur', '1',
         None, 20.0, None),
        (13, 1, 'Einführung in die Programmierung mit Python', 'DLBDSIPWP01_D', 5, 'Bestanden', 1.3, 'Klausur', '1',
         '28.11.2025', 92.2, None),
        (14, 1, 'Einführung in das wissenschaftliche Arbeiten für IT und Technik', 'DLBWIRITT01', 5, 'Bestanden', 2.5,
         'Klausur', '1', None, 65.0, None),
        (15, 1, 'Projekt: Objektorientierte und funktionale Programmierung mit Python', 'DLBDSOOFPP01_D', 5,
         'Bestanden', 2.0, 'Klausur', '2', None, 70.0, None),
        (16, 2, 'Einführung in die Netzwerkforensik', 'DLBCSEINF01', 5, 'Bestanden', 2.2, 'Klausur', '1', None, 79.0,
         None),
        (17, 2, 'Mathematik Grundlagen', 'IMT505', 5, 'Bestanden', 1.7, 'Klausur', '1', None, 89.0, None),
        (18, 2, 'Statistik - Wahrscheinlichkeit und deskriptive Statistik', 'DLBOSSPD501_D', 5, 'Bestanden', 1.5,
         'Klausur', '1', None, 93.0, None),
        (19, 2, 'Requirements Engineering', 'IREND01', 5, 'Bestanden', 2.0, 'Klausur', '1', None, 90.0, None),
        (20, 2, 'Projekt: Agiles Projektmanagement', 'DLBAPMEL01', 5, 'Bestanden', 3.5, 'Klausur', '1', None, 63.0,
         None),
        (21, 3, 'Grundzüge des System-Pentestings', 'DLBESESPB01_D', 5, 'In Arbeit', None, None, None, None, None,
         None),
        (22, 3, 'Theoretische Informatik und Mathematische Logik', 'DLBITML01', 5, 'Bestanden', 2.3, 'Klausur', '1',
         None, 79.0, None),
        (23, 3, 'Social Engineering und Insider Threats', 'DLBCSEESED1_D', 5, 'Bestanden', 3.0, 'Klausur', '1', None,
         60.0, None),
        (24, 3, 'Technische und betriebliche IT-Sicherheitskonzeptionen', 'DLBCSEEISC01_D', 5, 'In Arbeit', None, None,
         None, None, None, None),
        (25, 3, 'Projekt: Social Engineering', 'DLBCSEESED_D', 5, 'In Arbeit', None, None, None, None, None, None),
        (26, 4, 'DevSecOps und gängige Software-Schwachstellen', 'DLBCSEDC SW01_D', 5, 'Geplant', None, None, None,
         None, None, None),
        (27, 4, 'Kryptografische Verfahren', 'DLBISIC02_01', 5, 'Geplant', None, None, None, None, None, None),
        (28, 4, 'Host- und Softwareforensik', 'DLBCSEHSF01_D', 5, 'Geplant', None, None, None, None, None, None),
        (29, 4, 'Seminar: Aktuelle Themen in Computer Science', 'DLBCSCTC501_D', 5, 'Geplant', None, None, None, None,
         None, None),
        (30, 4, 'Projekt: Einsatz und Konfiguration von SIEM-Systemen', 'DLBCSEEISC01_D', 5, 'Geplant', None, None,
         None, None, None, None),
        (31, 5, 'Threat Modeling', 'DLBCSEEFT01_D', 5, 'Geplant', None, None, None, None, None, None),
        (32, 5, 'Standards der Informationssicherheit', 'DLBCSEISS01_D', 5, 'Geplant', None, None, None, None, None,
         None),
        (33, 5, 'Projekt: Threat Modeling', 'DLBCSEEFT01_D', 5, 'Geplant', None, None, None, None, None, None),
        (34, 6, 'Projekt: Allgemeine Programmierung mit C/C++', 'DLBMINPAPCC01', 5, 'Geplant', None, None, None, None,
         None, None),
        (35, 6, 'Bachelorarbeit', 'BBAK0I', 9, 'Geplant', None, None, None, None, None, None),
        (36, 6, 'Kolloquium', 'BBAK02', 1, 'Geplant', None, None, None, None, None, None),
        # Wahlpflichtbereich A
        (51, None, 'Cloud Computing', None, 5, 'Geplant', None, None, None, None, None, 'A'),
        (52, 5, 'Static and Dynamic Malware Analysis', None, 5, 'Geplant', None, None, None, None, None, 'A'),
        (53, 6, 'Principles of Ethical Hacking', None, 5, 'Geplant', None, None, None, None, None, 'A'),
        (54, 5, 'Grundlagen der objektorientierten Programmierung mit Java', None, 5, 'Geplant', None, None, None, None,
         None, 'A'),
        (55, None, 'Techniken und Methoden der agilen Softwareentwicklung', None, 5, 'Geplant', None, None, None, None,
         None, 'A'),
        (56, None, 'Attack Models and Threat Feeds', None, 5, 'Geplant', None, None, None, None, None, 'A'),
        (57, None, 'Mobile Software Engineering', None, 5, 'Geplant', None, None, None, None, None, 'A'),
        (58, None, 'Funk- und Telekommunikationssicherheit', None, 5, 'Geplant', None, None, None, None, None, 'A'),
        (59, None, 'Protocols, Log- and Dataflow-Analysis in Depth', None, 5, 'Geplant', None, None, None, None, None,
         'A'),
        (60, None, 'Smart Factory', None, 5, 'Geplant', None, None, None, None, None, 'A'),
        (61, None, 'Fertigungsverfahren Industrie 4.0', None, 5, 'Geplant', None, None, None, None, None, 'A'),
        (62, None, 'Einführung in das Internet of Things', None, 5, 'Geplant', None, None, None, None, None, 'A'),
        (63, None, 'Grundlagen der industriellen Softwaretechnik', None, 5, 'Geplant', None, None, None, None, None,
         'A'),
        # Wahlpflichtbereich B
        (64, None, 'Security Controls in the Cloud', None, 5, 'Geplant', None, None, None, None, None, 'B'),
        (65, 2, 'Project: Security by Design in the Cloud', None, 5, 'Geplant', None, None, None, None, None, 'B'),
        (66, None, 'Seminar: Sandbox Interpretation', None, 5, 'Geplant', None, None, None, None, None, 'B'),
        (67, None, 'Project: Pentesting', None, 5, 'Geplant', None, None, None, None, None, 'B'),
        (68, 4, 'Algorithmen, Datenstrukturen und Programmiersprachen', None, 5, 'Geplant', None, None, None, None,
         None, 'B'),
        (69, 6, 'Projekt: Agiles DevSecOps-Software-Engineering', None, 5, 'Geplant', None, None, None, None, None,
         'B'),
        (70, None, 'Project: Defense against APTs', None, 5, 'Geplant', None, None, None, None, None, 'B'),
        (71, None, 'Projekt: Mobile Software Engineering', None, 5, 'Geplant', None, None, None, None, None, 'B'),
        (72, None, 'Softwarearchitektur mobiler Geräte', None, 5, 'Geplant', None, None, None, None, None, 'B'),
        (73, None, 'Seminar: Threat Hunting, Analysis and Incident Response', None, 5, 'Geplant', None, None, None,
         None, None, 'B'),
        (74, None, 'Projekt: Smart Devices & Factory', None, 5, 'Geplant', None, None, None, None, None, 'B'),
        (75, None, 'Automatisierung und Robotics', None, 5, 'Geplant', None, None, None, None, None, 'B'),
        (76, None, 'Sicherheit im Internet of Things', None, 5, 'Geplant', None, None, None, None, None, 'B'),
        (77, None, 'Datenmodellierung und Datenbanksysteme', None, 5, 'Geplant', None, None, None, None, None, 'B'),
        (78, None, 'Studium Generale I', None, 5, 'Geplant', None, None, None, None, None, 'B'),
        (79, None, 'Studium Generale II', None, 5, 'Geplant', None, None, None, None, None, 'B'),
        # Wahlpflichtbereich C
        (80, 1, 'Kollaboratives Arbeiten', None, 5, 'Bestanden', 1.9, 'Klausur', '1', None, 89.0, 'C'),
        (81, None, 'Interkulturelle und ethische Handlungskompetenzen', None, 5, 'Geplant', None, None, None, None,
         None, 'C'),
        (82, None, 'Konfliktmanagement und Mediation', None, 5, 'Geplant', None, None, None, None, None, 'C'),
        (83, 6, 'Interaktion und Kommunikation in Organisationen', None, 5, 'Geplant', None, None, None, None, None,
         'C'),
        (84, 3, 'Business Intelligence', None, 5, 'In Arbeit', None, None, None, None, None, 'C'),
        (85, 5, 'Projekt: KI-Exzellenz mit kreativen Prompt-Techniken', None, 5, 'Geplant', None, None, None, None,
         None, 'C'),
    ]

    for d in test_daten:
        # Modul-Basis (ID, Semester, Name, Code, ECTS, Status)
        cursor.execute("INSERT INTO modul (id, semester_id, name, code, ects, status) VALUES (?, ?, ?, ?, ?, ?)",
                       (d[0], d[1], d[2], d[3], d[4], d[5]))

        # Falls Note vorhanden (Bestanden/Nicht bestanden)
        if d[6] is not None:
            cursor.execute(
                "INSERT INTO pruefungsleistung (modul_id, punkte, note, datum, versuch, pruefungsart) VALUES (?, ?, ?, ?, ?, ?)",
                (d[0], d[10], d[6], d[9], d[8], d[7]))

        # Falls Wahlpflichtbereich (A, B oder C)
        if d[11] is not None:
            cursor.execute("INSERT INTO wahlpflicht_modul (modul_id, bereich) VALUES (?, ?)", (d[0], d[11]))

    conn.commit()
