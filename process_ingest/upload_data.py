'''
Retrieve data from hugging face
'''
import os
from huggingface_hub import HfApi
from pathlib import Path

project_dir = Path(__file__).resolve().parent.parent
data_dir = project_dir / 'data'

api = HfApi(token=os.environ['HF_TOKEN'])

api.upload_folder(
    folder_path=data_dir,
    repo_id='cryogars/penetrometer_data',
    repo_type='dataset',
    path_in_repo='data'
)