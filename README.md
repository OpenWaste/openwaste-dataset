# openwaste-dataset

## Installation

```bash
git clone git@github.com:OpenWaste/openwaste-dataset.git
cd openwaste-dataset
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY="YOUR_KEY"
python utils/generate-images.py prompts/prompts.csv
```