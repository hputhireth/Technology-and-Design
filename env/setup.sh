# Setup during log in (one time off).
# source env/paths.sh && bash env/setup.sh
set -euo pipefail
mkdir -p "$COS_ROOT"/{hf_cache,data/raw/predict,data/cache,features,results,logs}
python -m venv "$COS_ROOT/venv"
source "$COS_ROOT/venv/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt
HF_HUB_OFFLINE=0 TRANSFORMERS_OFFLINE=0 python -c "from huggingface_hub import snapshot_download; snapshot_download('BAAI/bge-large-en-v1.5', allow_patterns=['*.json', '*.txt', 'model.safetensors'])"
echo "environment ready under $COS_ROOT"
