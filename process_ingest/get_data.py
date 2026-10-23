'''
Download project data from Hugging Face.
'''

from pathlib import Path
from huggingface_hub import snapshot_download

PROJECT_DIR = Path(__file__).resolve().parent.parent
REPO_ID = "cryogars/penetrometer_data"

print(f"Downloading data from: https://huggingface.co/datasets/{REPO_ID}")
print(f"Saving into project directory: {PROJECT_DIR}")

snapshot_download(
    repo_id=REPO_ID,
    repo_type="dataset",
    local_dir=PROJECT_DIR,
)

print("Download complete.")
print(f"Data should now be available at: {PROJECT_DIR / 'data'}")