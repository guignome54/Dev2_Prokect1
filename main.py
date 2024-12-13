import os
import time
import csv
from datetime import datetime
import argparse
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import cmd


class GestionFichiers:
    @staticmethod
    def obtenir_metadonnees(repertoire):
        """
        Retourne une liste de dictionnaires contenant les métadonnées des fichiers dans un répertoire.

        Préconditions:
        - `repertoire` doit exister, être un chemin valide et accessible.
        - L'utilisateur doit avoir les droits nécessaires pour accéder au répertoire.

        Postconditions:
        - Retourne une liste de dictionnaires contenant les métadonnées des fichiers présents dans le répertoire.
        - Les fichiers non accessibles ou avec des permissions restreintes sont ignorés.

        Erreurs possibles:
        - `FileNotFoundError`: Le répertoire n'existe pas.
        - `PermissionError`: L'accès au répertoire est refusé.
        """
        metadonnees_fichiers = []

        try:
            for nom_fichier in os.listdir(repertoire):
                chemin_complet = os.path.join(repertoire, nom_fichier)

                if os.path.isfile(chemin_complet):
                    taille = os.path.getsize(chemin_complet)
                    date_creation = datetime.fromtimestamp(os.path.getctime(chemin_complet)).strftime('%Y-%m-%d %H:%M:%S')
                    date_modification = datetime.fromtimestamp(os.path.getmtime(chemin_complet)).strftime('%Y-%m-%d %H:%M:%S')

                    metadonnees_fichiers.append({
                        'nom': nom_fichier,
                        'date_creation': date_creation,
                        'date_modification': date_modification,
                        'taille': taille
                    })
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Le répertoire '{repertoire}' n'existe pas.") from e
        except PermissionError as e:
            raise PermissionError(f"Permission refusée pour accéder au répertoire '{repertoire}'.") from e

        return metadonnees_fichiers

    @staticmethod
    def lire_csv(fichier_csv):
        """
        Lit les données existantes d'un fichier CSV et retourne un dictionnaire avec le nom du fichier comme clé.

        Préconditions:
        - `fichier_csv` doit exister et être accessible.
        - Le fichier doit être au format CSV valide avec les colonnes attendues.

        Postconditions:
        - Retourne un dictionnaire où chaque clé est le nom du fichier, et la valeur est un dictionnaire des métadonnées.

        Erreurs possibles:
        - `FileNotFoundError`: Le fichier CSV n'existe pas.
        - `PermissionError`: Le fichier CSV ne peut pas être lu.
        - `csv.Error`: Le fichier CSV contient une structure invalide.
        """
        donnees_existantes = {}
        if os.path.exists(fichier_csv):
            try:
                with open(fichier_csv, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        donnees_existantes[row['Nom du fichier']] = row
            except FileNotFoundError as e:
                raise FileNotFoundError(f"Le fichier CSV '{fichier_csv}' n'existe pas.") from e
            except PermissionError as e:
                raise PermissionError(f"Impossible d'accéder au fichier CSV '{fichier_csv}'.") from e
            except csv.Error as e:
                raise ValueError(f"Le fichier CSV '{fichier_csv}' est mal formé.") from e

        return donnees_existantes

    @staticmethod
    def ecrire_csv(metadonnees, fichier_csv):
        """
        Écrit ou met à jour les métadonnées dans un fichier CSV sans doublons.

        Préconditions:
        - `metadonnees` doit être une liste de dictionnaires avec les clés 'nom', 'date_creation', 'date_modification', et 'taille'.
        - `fichier_csv` doit être accessible en écriture.

        Postconditions:
        - Les métadonnées sont ajoutées ou mises à jour dans le fichier CSV.
        - Les données existantes dans le CSV sont conservées et mises à jour.

        Erreurs possibles:
        - `PermissionError`: Le fichier CSV ne peut pas être écrit.
        - `csv.Error`: Échec de l'écriture dans le fichier CSV.
        """
        donnees_existantes = GestionFichiers.lire_csv(fichier_csv)

        try:
            for donnee in metadonnees:
                donnees_existantes[donnee['nom']] = {
                    'Nom du fichier': donnee['nom'],
                    'Date de création': donnee['date_creation'],
                    'Date de modification': donnee['date_modification'],
                    'Taille (octets)': donnee['taille']
                }

            with open(fichier_csv, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Nom du fichier', 'Date de création', 'Date de modification', 'Taille (octets)']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for row in donnees_existantes.values():
                    writer.writerow(row)
        except PermissionError as e:
            raise PermissionError(f"Impossible d'écrire dans le fichier CSV '{fichier_csv}'.") from e
        except csv.Error as e:
            raise ValueError(f"Erreur lors de l'écriture dans le fichier CSV '{fichier_csv}'.") from e



class Surveillance(FileSystemEventHandler):
    def __init__(self, log_file, fichier_csv=None):
        self.log_file = log_file
        self.fichier_csv = fichier_csv

    def on_created(self, event):
        if not event.is_directory:
            self.log_event(event, "Créé")

    def on_deleted(self, event):
        if not event.is_directory:
            self.log_event(event, "Supprimé")

    def on_modified(self, event):
        if not event.is_directory:
            self.log_event(event, "Modifié")

    def log_event(self, event, action):
        """
        Enregistre un événement de fichier dans le log et met à jour le fichier CSV.

        Préconditions:
        - `event` doit contenir un chemin valide vers un fichier ou répertoire.
        - `action` doit être une chaîne décrivant l'événement ('Créé', 'Modifié', 'Supprimé').

        Postconditions:
        - L'événement est consigné dans le fichier log.
        - Si applicable, les métadonnées des fichiers sont mises à jour dans le CSV.

        Erreurs possibles:
        - `PermissionError`: Échec d'écriture dans le fichier log ou CSV.
        """
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {action}: {event.src_path}\n")
        except Exception as e:
            raise IOError(f"Erreur lors de l'écriture dans le fichier log {self.log_file}: {e}")



class Shell(cmd.Cmd):
    intro = 'Bienvenue dans le shell interactif. Tapez help ou ? pour lister les commandes.\n'
    prompt = '(shell) '

    def do_scan(self, arg):
        try:
            args = arg.split()
            if len(args) != 2:
                raise ValueError("Usage: scan <repertoire> <fichier_csv>")
            repertoire, fichier_csv = args
            metadonnees = GestionFichiers.obtenir_metadonnees(repertoire)
            GestionFichiers.ecrire_csv(metadonnees, fichier_csv)
            print(f"Métadonnées enregistrées dans {fichier_csv}.")
        except Exception as e:
            print(f"Erreur: {e}")

    def do_watch(self, arg):
        try:
            args = arg.split()
            if len(args) != 3:
                raise ValueError("Usage: watch <repertoire> <fichier_log> <fichier_csv>")
            repertoire, fichier_log, fichier_csv = args
            if not os.path.isdir(repertoire):
                raise ValueError(f"Le répertoire {repertoire} n'existe pas.")
            event_handler = Surveillance(fichier_log, fichier_csv)
            observer = Observer()
            observer.schedule(event_handler, path=repertoire, recursive=True)
            observer.start()
            print("Surveillance en cours... Appuyez sur Ctrl+C pour arrêter.")
            observer.join()
        except KeyboardInterrupt:
            print("\nArrêt de la surveillance.")
        except Exception as e:
            print(f"Erreur: {e}")


def main():
    parser = argparse.ArgumentParser(description="Script pour extraire et surveiller les métadonnées des fichiers.")
    parser.add_argument('--shell', action='store_true', help='Lance le shell interactif.')
    args = parser.parse_args()
    if args.shell:
        Shell().cmdloop()


if __name__ == "__main__":
    main()
