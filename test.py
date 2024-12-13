import unittest
import os
import shutil
import csv
from datetime import datetime
from main import GestionFichiers, Surveillance


class TestGestionFichiers(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Créer un répertoire temporaire et des fichiers pour les tests."""
        cls.test_dir = "test_dir"
        cls.test_csv = "test_metadata.csv"
        os.makedirs(cls.test_dir, exist_ok=True)

        # Créer des fichiers de test
        cls.file_1 = os.path.join(cls.test_dir, "file1.txt")
        cls.file_2 = os.path.join(cls.test_dir, "file2.txt")

        with open(cls.file_1, "w") as f:
            f.write("Contenu du fichier 1.")
        with open(cls.file_2, "w") as f:
            f.write("Contenu du fichier 2.")

    @classmethod
    def tearDownClass(cls):
        """Supprimer les fichiers et répertoires après les tests."""
        shutil.rmtree(cls.test_dir)
        if os.path.exists(cls.test_csv):
            os.remove(cls.test_csv)

    def test_obtenir_metadonnees(self):
        """Tester la récupération des métadonnées des fichiers."""
        metadonnees = GestionFichiers.obtenir_metadonnees(self.test_dir)
        self.assertEqual(len(metadonnees), 2)
        self.assertTrue(any(f['nom'] == "file1.txt" for f in metadonnees))
        self.assertTrue(any(f['nom'] == "file2.txt" for f in metadonnees))

    def test_ecrire_et_lire_csv(self):
        """Tester l'écriture et la lecture des métadonnées dans un fichier CSV."""
        metadonnees = GestionFichiers.obtenir_metadonnees(self.test_dir)
        GestionFichiers.ecrire_csv(metadonnees, self.test_csv)

        # Vérifier que le fichier CSV a été créé
        self.assertTrue(os.path.exists(self.test_csv))

        # Lire les données et valider leur contenu
        donnees_csv = GestionFichiers.lire_csv(self.test_csv)
        self.assertIn("file1.txt", donnees_csv)
        self.assertIn("file2.txt", donnees_csv)
        self.assertEqual(donnees_csv["file1.txt"]["Nom du fichier"], "file1.txt")

    def test_lire_csv_inexistant(self):
        """Tester la lecture d'un fichier CSV inexistant."""
        donnees = GestionFichiers.lire_csv("fichier_inexistant.csv")
        self.assertEqual(donnees, {})

    def test_ecrire_csv_erreur(self):
        """Tester une erreur lors de l'écriture dans un fichier CSV."""
        with self.assertRaises(IOError):
            GestionFichiers.ecrire_csv([], "/chemin/invalide.csv")


class TestSurveillance(unittest.TestCase):

    def setUp(self):
        """Créer un fichier log temporaire pour les tests."""
        self.log_file = "test_log.log"
        self.csv_file = "test_watch.csv"
        open(self.log_file, "w").close()  # Fichier vide pour les logs

    def tearDown(self):
        """Nettoyer les fichiers après chaque test."""
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
        if os.path.exists(self.csv_file):
            os.remove(self.csv_file)

    def test_log_event(self):
        """Tester la journalisation d'un événement."""
        handler = Surveillance(self.log_file)
        event_mock = type("Event", (object,), {"src_path": "/test/file.txt"})()
        handler.log_event(event_mock, "Créé")

        # Vérifier le contenu du fichier log
        with open(self.log_file, "r", encoding="utf-8") as f:
            logs = f.read()
        self.assertIn("Créé: /test/file.txt", logs)

if __name__ == "__main__":
    unittest.main()
