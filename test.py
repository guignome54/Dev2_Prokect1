import csv

# Exemple de factures
factures = [
    {
        "nom": "facture1.pdf",
        "date_creation": "2024-01-01T10:00:00",
        "date_modification": "2024-01-02T12:00:00",
        "taille": 1024
    },
    {
        "nom": "facture2.pdf",
        "date_creation": "2024-02-01T10:00:00",
        "date_modification": "2024-02-02T12:00:00",
        "taille": 2048
    }
]

# Écriture du fichier CSV
with open('metadonnees_factures.csv', 'w', newline='') as fichier:
    writer = csv.DictWriter(fichier, fieldnames=["nom", "date_creation", "date_modification", "taille"])
    writer.writeheader()
    for facture in factures:
        writer.writerow(facture)

print("Fichier de métadonnées CSV créé avec succès.")
