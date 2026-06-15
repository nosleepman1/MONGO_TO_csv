import io
import re
from typing import List, Dict, Any
import pandas as pd

def clean_data(docs: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Normalise les documents MongoDB en DataFrame pandas propre :
    - Exclut la colonne '_id'
    - Aplatit les structures de dictionnaires imbriquées (ex: user.name)
    - Joint les listes/tableaux sous forme de chaînes de caractères séparées par des virgules (ex: tags)
    """
    if not docs:
        return pd.DataFrame()
        
    # Normalise les structures imbriquées (dictionnaires)
    df = pd.json_normalize(docs)
    
    # Exclure le champ _id s'il est présent
    if "_id" in df.columns:
        df = df.drop(columns=["_id"])
        
    # Traiter les listes (ex: tags, arrays) pour les transformer en chaînes propres séparées par des virgules
    for col in df.columns:
        # On vérifie si au moins une ligne de cette colonne contient une liste
        if df[col].apply(lambda x: isinstance(x, list)).any():
            df[col] = df[col].apply(
                lambda x: ", ".join(map(str, x)) if isinstance(x, list) else x
            )
            
    return df


def generate_csv_bytes(df: pd.DataFrame) -> bytes:
    """
    Génère le contenu CSV en mémoire sous forme de bytes encodés en UTF-8-SIG (avec BOM).
    Évite le doublon de BOM en écrivant d'abord en texte brut, puis en encodant.
    """
    stream = io.StringIO()
    df.to_csv(stream, index=False)  # Écrit le texte brut sans insérer de BOM
    csv_text = stream.getvalue()
    return csv_text.encode("utf-8-sig")  # Encode en UTF-8 et ajoute l'en-tête BOM


def sanitize_filename(name: str) -> str:
    """
    Assainit un nom de fichier pour éviter les erreurs de téléchargement
    et d'en-tête HTTP sur certains navigateurs en remplaçant les caractères non autorisés.
    """
    # Remplace les caractères non autorisés sous Windows/Linux par des tirets bas
    sanitized = re.sub(r'[\\/*?:"<>|]', "_", name)
    return sanitized
