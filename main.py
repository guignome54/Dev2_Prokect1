import argparse
import cmd
import csv
import os
import sqlite3
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

# Configurer le logger
logging.basicConfig(filename='file_monitor.log', level=logging.INFO,
                    format='%(asctime)s - %(message)s')

# Fonction pour extraire les métadonnées d'un fichier
def get_file_metadata(file_path):
    stat = os.stat(file_path)
    return {
        'name': os.path.basename(file_path),
        'creation_date': time.ctime(stat.st_ctime),
        'modification_date': time.ctime(stat.st_mtime),
        'size': stat.st_size
    }

# Classe pour gérer les événements de modification des fichiers
class FileEventHandler(FileSystemEventHandler):
    def __init__(self, db_type, db_path):
        self.db_type = db_type
        self.db_path = db_path

    def process_event(self, event, event_type):
        file_path = event.src_path
        if os.path.isfile(file_path):
            metadata = get_file_metadata(file_path)
            log_message = f"{event_type} - {file_path}: {metadata}"
            logging.info(log_message)
            if self.db_type == 'csv':
                self.update_csv(metadata)
            elif self.db_type == 'sqlite':
                self.update_sqlite(metadata)
            # Ajouter ici les actions spécifiques à exécuter (bonus)

    def update_csv(self, metadata):
        file_exists = os.path.isfile(self.db_path)
        with open(self.db_path, 'a', newline='') as csvfile:
            fieldnames = ['name', 'creation_date', 'modification_date', 'size']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(metadata)

    def update_sqlite(self, metadata):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_metadata (
                name TEXT,
                creation_date TEXT,
                modification_date TEXT,
                size INTEGER
            )
        ''')
        cursor.execute('''
            INSERT INTO file_metadata (name, creation_date, modification_date, size)
            VALUES (?, ?, ?, ?)
        ''', (metadata['name'], metadata['creation_date'], metadata['modification_date'], metadata['size']))
        conn.commit()
        conn.close()

    def on_created(self, event):
        self.process_event(event, "Création")

    def on_modified(self, event):
        self.process_event(event, "Modification")

    def on_deleted(self, event):
        file_path = event.src_path
        log_message = f"Suppression - {file_path}"
        logging.info(log_message)
        if self.db_type == 'csv':
            self.remove_from_csv(file_path)
        elif self.db_type == 'sqlite':
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM file_metadata WHERE name = ?', (os.path.basename(file_path),))
            conn.commit()
            conn.close()

    def remove_from_csv(self, file_path):
        rows = []
        file_exists = os.path.isfile(self.db_path)
        if file_exists:
            with open(self.db_path, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row['name'] != os.path.basename(file_path):
                        rows.append(row)
            with open(self.db_path, 'w', newline='') as csvfile:
                fieldnames = ['name', 'creation_date', 'modification_date', 'size']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

# Interface en ligne de commande
class FileMonitorShell(cmd.Cmd):
    intro = 'Bienvenue dans le shell de surveillance des fichiers. Tapez help ou ? pour voir les commandes disponibles.\n'
    prompt = '(file-monitor) '

    def do_start(self, arg):
        'Démarrer la surveillance: start <répertoire> <csv/sqlite> <chemin_du_fichier_db>'
        try:
            args = arg.split()
            if len(args) != 3:
                raise ValueError("Nombre d'arguments incorrect")
            directory, db_type, db_path = args
            if db_type not in ['csv', 'sqlite']:
                raise ValueError("Type de base de données invalide")
            start_monitoring(directory, db_type, db_path)
        except Exception as e:
            print(f"Erreur: {e}")

    def do_exit(self, arg):
        'Quitter le shell: exit'
        print('Arrêt du shell de surveillance des fichiers.')
        return True

# Fonction pour démarrer la surveillance
def start_monitoring(directory, db_type, db_path):
    event_handler = FileEventHandler(db_type, db_path)
    observer = Observer()
    observer.schedule(event_handler, directory, recursive=True)
    observer.start()
    print(f"Surveillance du répertoire {directory} commencée. Appuyez sur Ctrl+C pour arrêter.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# Analyseur d'arguments
def main():
    parser = argparse.ArgumentParser(description="Script de surveillance des fichiers.")
    parser.add_argument('directory', help="Répertoire à surveiller")
    parser.add_argument('db_type', choices=['csv', 'sqlite'], help="Type de base de données (csv ou sqlite)")
    parser.add_argument('db_path', help="Chemin du fichier de base de données")
    args = parser.parse_args()

    shell = FileMonitorShell()
    shell.cmdloop()

if __name__ == "__main__":
    main()
