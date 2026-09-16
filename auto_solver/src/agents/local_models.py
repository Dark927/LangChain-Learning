import os
import requests
from threading import Thread

# Recommended Local Models (GGUF format for GPT4All)
RECOMMENDED_MODELS = [
    {
        "name": "Llama 3 (8B)",
        "filename": "Meta-Llama-3-8B-Instruct.Q4_0.gguf",
        "url": "https://gpt4all.io/models/gguf/Meta-Llama-3-8B-Instruct.Q4_0.gguf",
        "size_gb": 4.6
    },
    {
        "name": "Phi-3 Mini (3.8B)",
        "filename": "Phi-3-mini-4k-instruct.Q4_0.gguf",
        "url": "https://gpt4all.io/models/gguf/Phi-3-mini-4k-instruct.Q4_0.gguf",
        "size_gb": 2.4
    },
    {
        "name": "DeepSeek R1 Distill Qwen (7B)",
        "filename": "DeepSeek-R1-Distill-Qwen-7B-Q4_0.gguf",
        "url": "https://huggingface.co/bartowski/DeepSeek-R1-Distill-Qwen-7B-GGUF/resolve/main/DeepSeek-R1-Distill-Qwen-7B-Q4_0.gguf",
        "size_gb": 4.3
    },
    {
        "name": "Mistral (7B)",
        "filename": "mistral-7b-instruct-v0.1.Q4_0.gguf",
        "url": "https://gpt4all.io/models/gguf/mistral-7b-instruct-v0.1.Q4_0.gguf",
        "size_gb": 4.1
    }
]

def get_models_dir():
    from core.config import config
    d = os.path.join(config._get_data_dir(), "models")
    os.makedirs(d, exist_ok=True)
    return d

def get_installed_models():
    d = get_models_dir()
    installed = []
    if not os.path.exists(d): return installed
    for f in os.listdir(d):
        if f.endswith('.gguf'):
            pretty_name = f
            for rm in RECOMMENDED_MODELS:
                if rm["filename"] == f:
                    pretty_name = rm["name"]
                    break
            installed.append({"name": pretty_name, "filename": f, "path": os.path.join(d, f)})
    return installed

def delete_model(filename: str):
    d = get_models_dir()
    p = os.path.join(d, filename)
    if os.path.exists(p):
        os.remove(p)

def download_model_async(url: str, filename: str, progress_callback, completion_callback, error_callback):
    def _download():
        try:
            d = get_models_dir()
            dest = os.path.join(d, filename)
            temp_dest = dest + ".download"
            
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            
            downloaded = 0
            with open(temp_dest, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024*1024): # 1MB chunks
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress_callback(downloaded / total_size)
            
            os.rename(temp_dest, dest)
            completion_callback()
        except Exception as e:
            error_callback(str(e))
            
    Thread(target=_download, daemon=True).start()
