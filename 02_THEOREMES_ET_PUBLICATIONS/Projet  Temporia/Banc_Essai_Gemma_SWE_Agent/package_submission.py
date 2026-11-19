#!/usr/bin/env python3
"""
Packaging Script: Creates submission.zip for the Kaggle Gemma 4 Developer Agent Competition
"""

import os
import zipfile

def package_submission():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    source_dir = os.path.join(base_dir, "kaggle_submission")
    zip_path = os.path.join(base_dir, "submission.zip")
    
    print("[1/3] Verification des fichiers de soumission dans kaggle_submission/...")
    required_files = [
        os.path.join(source_dir, "agent.yaml"),
        os.path.join(source_dir, "configs", "sampling.yaml"),
        os.path.join(source_dir, "prompts", "system_prompt.txt")
    ]
    
    for f in required_files:
        if not os.path.exists(f):
            raise FileNotFoundError(f"Fichier requis manquant : {f}")
        print(f"   [OK] {os.path.relpath(f, base_dir)}")
        
    print("[2/3] Compression dans submission.zip...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                archive_name = os.path.relpath(file_path, source_dir)
                zipf.write(file_path, archive_name)
                print(f"   + {archive_name}")
                
    print(f"[3/3] Validation reussie : {zip_path} ({os.path.getsize(zip_path)} octets)")
    print("Pret pour soumission directe sur Kaggle !")

if __name__ == "__main__":
    package_submission()
