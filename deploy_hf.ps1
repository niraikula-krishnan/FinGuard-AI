# Deploy FinGuard-AI to Hugging Face (free Static Space)
Write-Host "Deploying static demo to HF Space (free, no Docker/Pro required)..."
$src = Join-Path $PSScriptRoot "hf_deploy"
if (-not (Test-Path $src)) { Write-Error "hf_deploy folder not found"; exit 1 }

Write-Host "Log in if needed (paste Write token from https://huggingface.co/settings/tokens)"
hf auth login

Push-Location $src
hf upload niraikula-krishnan/FinGuard-AI . . --repo-type space --commit-message "Deploy FinGuard-AI static demo"
Pop-Location

Write-Host ""
Write-Host "Live demo: https://huggingface.co/spaces/niraikula-krishnan/FinGuard-AI"
Write-Host "Direct app:  https://niraikula-krishnan-finguard-ai.hf.space"
