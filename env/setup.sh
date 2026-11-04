# Setup on a login node (one time off). Load the cluster's Python module first so the venv is built on it; the module name is
# recorded in venv/PYMOD and every job loads the same one.
#     module load <python module>   (for example the python/3.11 module; module avail python lists them)
#     source env/paths.sh && bash env/setup.sh
set -euo pipefail
mkdir -p "$COS_ROOT"/{hf_cache,data/raw/predict,data/cache,features,results,logs}
python -m venv "$COS_ROOT/venv"
source "$COS_ROOT/venv/bin/activate"
pip install --upgrade pip
pip install torch --index-url https://download.pytorch.org/whl/cu126   # the CUDA 12.6 wheels, the last that run on the P100
pip install -r requirements.txt
(module -t list 2>&1 | grep -i '^python' | head -1 > "$COS_ROOT/venv/PYMOD") || true
HF_HUB_OFFLINE=0 TRANSFORMERS_OFFLINE=0 python -c "from huggingface_hub import snapshot_download; snapshot_download('BAAI/bge-large-en-v1.5', allow_patterns=['*.json', '*.txt', 'model.safetensors'])"
echo "environment ready under $COS_ROOT; python module $(cat "$COS_ROOT/venv/PYMOD" 2>/dev/null || echo 'not recorded')"
