'''
Retrieve data from hugging face
'''
import os
from huggingface_hub import HfApi
from pathlib import Path

import os
from huggingface_hub import HfApi
from pathlib import Path

project_dir = Path(__file__).resolve().parent.parent
data_dir = project_dir / 'data'

hf_token = os.getenv('HF_TOKEN')

if not hf_token:
    raise RuntimeError(
        "Missing required environment variable HF_TOKEN. "
        "Set it to your Hugging Face access token before running this script."
    )

api = HfApi(token=hf_token)

api.upload_folder(
    folder_path=data_dir,
    repo_id='cryogars/penetrometer_data',
    repo_type='dataset',
    path_in_repo='data'
)