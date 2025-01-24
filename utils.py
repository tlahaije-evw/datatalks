import pandas as pd
import tiktoken

def get_dataset_preview(dataset_path, rows=1):
    """
    Leest een dataset en retourneert de eerste paar rijen als een HTML-tabel.
    """
    try:
        # Lees de dataset
        df = pd.read_excel(dataset_path)
        
        # Retourneer de eerste 'rows' rijen als HTML
        return df.head(rows).to_html(classes='table table-bordered table-sm', index=False)
    except Exception as e:
        return f"<p>Kan de dataset niet laden: {str(e)}</p>"

def calculate_tokens_with_preview(dataset_path, model="gpt-4", preview_rows=5):
    """
    Bereken het aantal tokens dat nodig is om een dataset-preview (header + voorbeelddata) naar AI te sturen.
    
    Args:
        dataset_path (str): Pad naar de dataset (bijv. CSV of Excel).
        model (str): Het AI-model waarvoor je de tokens wilt berekenen (bijv. 'gpt-4').
        preview_rows (int): Aantal voorbeeldrijen dat wordt opgenomen in de preview.
    
    Returns:
        tuple: (int, str): Het geschatte aantal tokens en de dataset-preview als string.
    """
    try:
        # Laad de dataset
        if dataset_path.endswith(".csv"):
            df = pd.read_csv(dataset_path)
        elif dataset_path.endswith((".xls", ".xlsx")):
            df = pd.read_excel(dataset_path)
        else:
            raise ValueError("Ondersteunt alleen CSV en Excel-bestanden.")

        # Maak een preview: alleen de kolomnamen en een paar rijen
        df_preview = df.head(preview_rows)

        # Zet de preview om naar een compact tekstformaat (CSV-achtige structuur)
        dataset_preview = df_preview.to_csv(index=False)

        # Gebruik de tokenizer voor het opgegeven model
        encoding = tiktoken.encoding_for_model(model)

        # Bereken het aantal tokens
        tokens = len(encoding.encode(dataset_preview))

        return tokens
    except Exception as e:
        print(f"Fout bij het berekenen van tokens: {e}")
        return None, None



