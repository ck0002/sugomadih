#!/usr/bin/env bash
# Local LLM for DnLLM: Qwen3.5 2B (Q4_K_M, ~1.3 GB) served by llama.cpp.
# First run downloads the model from Hugging Face into the llama.cpp cache.
# OpenAI-compatible API at http://localhost:8080/v1
exec llama-server \
  -hf unsloth/Qwen3.5-2B-GGUF:Q4_K_M \
  --no-mmproj \
  --port "${LLM_PORT:-8080}" \
  --ctx-size 8192 \
  --chat-template-kwargs '{"enable_thinking":false}' \
  "$@"
