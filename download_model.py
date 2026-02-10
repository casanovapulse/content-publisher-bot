import os
import requests
import zipfile

def download_vosk_model(model_name="vosk-model-small-en-us-0.15"):
    if os.path.exists(model_name):
        return model_name
        
    print(f"Downloading Vosk model: {model_name}...")
    url = f"https://alphacephei.com/vosk/models/{model_name}.zip"
    response = requests.get(url, stream=True)
    
    with open(f"{model_name}.zip", "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            
    print("Unzipping model...")
    with zipfile.ZipFile(f"{model_name}.zip", "r") as zip_ref:
        zip_ref.extractall(".")
        
    os.remove(f"{model_name}.zip")
    print("Vosk model ready.")
    return model_name

if __name__ == "__main__":
    download_vosk_model()
