# Agents Instructions - IndexTTS2

> **Última Atualização:** 2026-01-08
> **Projeto:** IndexTTS2 - Text-to-Speech para **Anime Studio Auto**

---

## 🎯 OBJETIVO DO PROJETO

IndexTTS2 é o motor TTS para produção de animes no **Anime-Studio-Auto**:
- **Voice Cloning** - Clonagem de voz zero-shot (vozes de personagens)
- **Emotion Control** - Controle emocional para cenas dramáticas
- **Duration Control** - Sincronização precisa com lip-sync
- **Multilingual** - Português BR + Japonês para anime

### Integração com Anime Studio
```
┌─────────────────────────────────────────────────────────────────┐
│  ANIME-STUDIO-AUTO PIPELINE (MULTI-GPU)                         │
├─────────────────────────────────────────────────────────────────┤
│  NÓ: gpu-node-3090 (Dual 3090)                                  │
│  ├─ GPU 0: [Inspector] Cosmos Reason (Vision)                   │
│  │  └─ Analisa referência, extrai beats visuais                 │
│  └─ GPU 1: [Director] LLM Local (Qwen 14B/32B)                  │
│     └─ Analisa roteiro, define emoções p/ TTS                   │
├─────────────────────────────────────────────────────────────────┤
│  NÓ: gpu-node-4090 (Single 4090)                                │
│  ├─ [Producer] IndexTTS2 + Wan 2.1 T2V                          │
│  └─ Gera Áudio Final (com emoção) e Vídeo Final                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🖥️ INFRAESTRUTURA

### Servidores Disponíveis (IPs Tailscale)

| Servidor             | Tailscale IP     | Hardware            | Uso no Pipeline                           |
| -------------------- | ---------------- | ------------------- | ----------------------------------------- |
| **dev-remote-01**    | `10.41.80.17`    | VM Linux            | **Desenvolvimento Principal** (IndexTTS2) |
| **gpu-node-4090**    | `100.114.21.15`  | RTX 4090 24GB       | IndexTTS2 + Wan T2V (Producer)            |
| **gpu-node-3090**    | `100.86.51.120`  | 2x RTX 3090 48GB    | Cosmos Reason + ComfyUI (Inspector)       |
| **data-services-01** | `100.103.114.73` | VM Linux            | PostgreSQL, Redis, Control Plane          |
| **gpac-teste-01**    | `100.67.24.51`   | 32 cores, 787GB RAM | LLM Qwen3-235B (Roteiros)                 |
| **minio-01~04**      | `100.109.125.15` | Cluster 4 nodes     | MinIO Object Storage (Assets)             |
| **macmini-m4-01**    | `100.72.90.72`   | M4 16GB             | MLX LLM API, Host WoL                     |
| **windows-wsl**      | `100.66.250.109` | RTX 5060 Ti Win     | Fonte de Dados (AnimeWwise)               |

### PC Windows (Fonte de Dados)

**Host:** `DESKTOP-5FKDHQF` | **IP:** `100.66.250.109` | **Alias SSH:** `windows-local`

```bash
# Acesso SSH por Certificado (sem senha!)
ssh windows-local

# Ou explicitamente:
ssh user@100.66.250.109

# Localização do AnimeWwise (12TB drive E:)
# E:\AnimeWwise\Genshin_JP\vo_freetalk\vo_*
# E:\AnimeWwise\ZZZ_JP\*
```

**Datasets Disponíveis:**
| Dataset    | Personagens | Caminho Windows                         |
| ---------- | ----------- | --------------------------------------- |
| Genshin_JP | 110+ chars  | `E:\AnimeWwise\Genshin_JP\vo_freetalk\` |
| Genshin_EN | ~100 chars  | `E:\AnimeWwise\Genshin_EN\`             |
| ZZZ_JP     | Ver 1.4-2.2 | `E:\AnimeWwise\ZZZ_JP\`                 |
| ZZZ_EN     | Ver 1.4-2.2 | `E:\AnimeWwise\ZZZ_EN\`                 |

### GPU Principal: `gpu-node-4090` (100.114.21.15)

**Status Atual:** ✅ Online - 24GB VRAM livres

**Hardware:**
- NVIDIA RTX 4090 (24GB VRAM)
- Ubuntu 24.04
- Docker + NVIDIA Container Toolkit
- CUDA 12.8 / Driver 580.95

**Workloads na 4090:**
1. **IndexTTS2** - TTS (~8GB FP16)
2. **Wan 2.1 T2V** - Geração de vídeo (~16GB)
3. **Treino LoRA** - musubi-tuner

**Requisitos IndexTTS2:**
- ~8GB VRAM (FP16) / ~14GB VRAM (FP32)
- PyTorch 2.8 + CUDA 12.8

---

## 🔧 ACESSO SSH

```bash
# GPU Node 4090 (principal para IndexTTS2)
ssh vmadmin@100.114.21.15

# GPU Node 3090 (backup)
ssh vmadmin@100.86.51.120

# Data Services
ssh vmadmin@100.103.114.73

# LLM Server (CPU)
ssh vmadmin@100.67.24.51
```

---

## ⚡ COMANDOS RÁPIDOS IndexTTS2

### Verificar GPU
```bash
# Verificar CUDA disponível
uv run tools/gpu_check.py

# Monitorar VRAM
nvidia-smi -l 1
```

### Rodar WebUI
```bash
# WebUI padrão (FP32)
uv run webui.py

# WebUI com FP16 (menor VRAM, recomendado)
uv run webui.py --fp16

# Ver todas as opções
uv run webui.py -h
```

### Inferência via Python
```python
from indextts.infer_v2 import IndexTTS2

tts = IndexTTS2(
    cfg_path="checkpoints/config.yaml", 
    model_dir="checkpoints", 
    use_fp16=True,  # Usar FP16 para menor VRAM
    use_cuda_kernel=False, 
    use_deepspeed=False
)

# Voice cloning simples
tts.infer(
    spk_audio_prompt='examples/voice_01.wav', 
    text="Olá, este é um teste!", 
    output_path="output.wav", 
    verbose=True
)

# Com controle emocional via áudio
tts.infer(
    spk_audio_prompt='examples/voice_07.wav', 
    text="Este texto será falado com emoção triste.",
    emo_audio_prompt='examples/emo_sad.wav',
    emo_alpha=0.9,
    output_path="output_sad.wav"
)

# Com controle emocional via vetor
# [happy, angry, sad, afraid, disgusted, melancholic, surprised, calm]
tts.infer(
    spk_audio_prompt='examples/voice_10.wav', 
    text="Que surpresa incrível!",
    emo_vector=[0, 0, 0, 0, 0, 0, 0.8, 0],  # Surprised
    output_path="output_surprised.wav"
)

# Com emoção baseada no texto
tts.infer(
    spk_audio_prompt='examples/voice_12.wav', 
    text="Corra! Eles estão vindo!",
    use_emo_text=True,
    emo_alpha=0.6,
    output_path="output_afraid.wav"
)
```

---

## 🎯 MELHORES PRÁTICAS (Pesquisa MCP)

> Fonte: Perplexity + Context7 (IndexTTS, index-tts-lora)

### Áudio de Referência (Voice Cloning)
| Parâmetro       | Recomendação                 |
| --------------- | ---------------------------- |
| **Duração**     | 3-10 segundos (máx ~1:30)    |
| **Sample Rate** | 16kHz+ (24kHz ideal)         |
| **Qualidade**   | Áudio limpo, sem ruído/eco   |
| **Conteúdo**    | Fala contínua, emoção neutra |

⚠️ **Textos longos**: Segmentar para evitar degradação de qualidade.

### Controle Emocional - 3 Modos

**1. Via Áudio de Referência (mais natural):**
```python
tts.infer(
    spk_audio_prompt='voz_personagem.wav',  # Timbre
    emo_audio_prompt='emoção_triste.wav',    # Emoção (outro speaker OK!)
    emo_alpha=0.9,  # 0.0-1.0 intensidade
    text="Texto com emoção aplicada"
)
```

**2. Via Vetor de Emoções (mais preciso):**
```python
# [happy, angry, sad, afraid, disgusted, melancholic, surprised, calm]
emo_vector = [0.3, 0, 0.5, 0, 0, 0.2, 0, 0]  # Mix: happy + sad + melancholic

tts.infer(
    spk_audio_prompt='voz.wav',
    emo_vector=emo_vector,
    use_random=False,  # True reduz fidelidade da clonagem
    text="Texto"
)
```

**3. Via Texto Natural (mais fácil):**
```python
tts.infer(
    spk_audio_prompt='voz.wav',
    use_emo_text=True,       # Detecta emoção do texto automaticamente
    emo_text="Estou com medo!",  # Ou define explicitamente
    emo_alpha=0.6,           # Recomendado ~0.6 para modo texto
    text="Corra! Eles estão vindo!"
)
```

### Otimização de Inferência

| Flag                   | Efeito                  | Recomendação                          |
| ---------------------- | ----------------------- | ------------------------------------- |
| `use_fp16=True`        | -50% VRAM, +velocidade  | ✅ **Sempre usar**                     |
| `use_cuda_kernel=True` | Kernels CUDA compilados | ⚠️ Requer build                        |
| `use_deepspeed=True`   | Acelera autogressivo    | ⚠️ Pode ser mais lento em alguns casos |

### LoRA Fine-Tuning (Vozes Personalizadas)

Para treinar vozes específicas de personagens:

**1. Preparar Dataset:**
```bash
# Criar lista: audio_list.txt
# /path/audio1.wav    Transcrição do áudio 1
# /path/audio2.wav    Transcrição do áudio 2

python tools/extract_codec.py \
    --audio_list data/personagem_audio_list.txt \
    --extract_condition \
    --output_dir finetune_data/personagem \
    --model_path checkpoints/gpt.pth \
    --device cuda
```

**2. Configurar Treino (config.yaml):**
```yaml
train:
  epochs: 15
  optimizer:
    learning_rate: 5.0e-5
  lora:
    r: 16              # Rank (8-32)
    lora_alpha: 32     # Scaling
    lora_dropout: 0.1
    target_modules:
      - "attn.c_attn"
      - "attn.c_proj"
      - "mlp.c_fc"
      - "mlp.c_proj"
```

**3. Treinar:**
```bash
python train.py
```

**Requisitos de Dataset:**
- Mínimo: ~30 minutos de áudio
- Ideal: 1-2 horas para máxima qualidade
- Transcrições precisas obrigatórias

### 📂 Fontes de Vozes (Assets)
Para clonagem de alta qualidade sem ruído:
1. **Jogos Gacha (Genshin/Star Rail/ZZZ)**:
   - **Ferramenta Recomendada**: [AnimeWwise](https://github.com/Escartem/AnimeWwise). Consegue extrair os áudios `.pck` recuperando os nomes originais dos arquivos.
   - **Seus Caminhos ZZZ**:
     - **Windows**: `E:\Epic\ZenlessZoneZero\ZenlessZoneZero_Data\StreamingAssets\Audio\Windows\Full`
     - **WSL/Linux**: `/mnt/e/Epic/ZenlessZoneZero/ZenlessZoneZero_Data/StreamingAssets/Audio/Windows/Full`
2. **Visual Novels**: Geralmente arquivos `.wav`/`.ogg` soltos na pasta do jogo.
3. **UVR5 (Ultimate Vocal Remover)**: Usar para limpar vozes de animes com música de fundo.

---

## 📁 ESTRUTURA DO PROJETO

```
IndexTTS2/
├── checkpoints/          # Pesos do modelo (~4.7GB total)
│   ├── gpt.pth          # GPT principal (~3.4GB)
│   ├── s2mel.pth        # Speech-to-Mel (~1.2GB)
│   ├── config.yaml      # Configuração
│   └── qwen0.6bemo4-merge/  # Modelo Qwen para emoções
├── indextts/            # Código fonte do modelo
│   ├── infer_v2.py      # IndexTTS2 (atual)
│   ├── infer.py         # IndexTTS1 (legado)
│   └── ...
├── examples/            # Áudios de exemplo
├── tools/               # Utilitários
├── webui.py             # Interface Gradio
└── pyproject.toml       # Dependências (uv)
```

---

## 🐛 PROBLEMAS CONHECIDOS

### Git LFS budget excedido
**Sintoma:** `git lfs pull` falha com "exceeded its LFS budget"  
**Solução:** Baixar exemplos do HuggingFace:
```bash
hf download IndexTeam/IndexTTS-2 --local-dir=checkpoints
```

### CUDA Out of Memory
**Sintoma:** `CUDA out of memory` durante inferência  
**Solução:**
1. Usar FP16: `use_fp16=True` ou `--fp16`
2. Reduzir batch size
3. Fechar outros processos GPU
4. Usar textos menores

### Áudio de má qualidade
**Causa:** Áudio de referência ruim  
**Solução:**
- Usar áudio limpo, sem ruído de fundo
- 3-10 segundos de duração ideal
- Sample rate 24kHz+ recomendado

---

## 🔗 INTEGRAÇÃO COM PIPELINE EXISTENTE

O IndexTTS2 pode substituir o XTTS v2 atual em `gpu-node-3090:8020`:

**Endpoint TTS atual (XTTS):**
```bash
curl -X POST "http://100.86.51.120:8020/tts_to_audio/" \
    -H "Content-Type: application/json" \
    -d '{"text": "Olá mundo", "language": "pt", "speaker_wav": "default"}' \
    -o output.wav
```

**IndexTTS2 como API:**
- Criar wrapper FastAPI para compatibilidade
- Suporta mesmos parâmetros + emoções
- Melhor qualidade de voz clonada

---

## 📋 CHECKLIST PRÉ-USO

- [ ] Checkpoints baixados em `checkpoints/`
- [ ] GPU com 8GB+ VRAM livre
- [ ] Ambiente uv sincronizado: `uv sync --all-extras`
- [ ] Áudios de exemplo disponíveis

---

## 📝 MANUTENÇÃO

### Após modificar projeto:
```bash
git add .
git commit -m "feat/fix/docs: [descrição]"
git push
```

### Atualizar dependências:
```bash
uv sync --all-extras --upgrade
```

---

## 🇧🇷 REGRA DE IDIOMA

**Todo conteúdo DEVE ser em Português do Brasil (pt-BR).**

- TTS: Suporta `pt`, `en`, `zh` e outros
- Código: Inglês (variáveis, funções)
- Documentação: Português BR

---

## 🏭 LORA FACTORY (Multi-Character Voice Generation)

Sistema para criar vozes originais misturando áudios de jogos (Genshin + ZZZ).

### Arquitetura Remota
```
PC Windows (100.66.250.109)        VM dev-remote-01           GPU gpu-node
E:\AnimeWwise\                     (Desenvolvimento)          (Treinamento)
├─ Genshin_JP (110+ chars)  ──SSH──►  source_audio/    ──►   trained_ckpts/
├─ Genshin_EN               ──────►  batch_ingest.py   ──►   S3 MinIO
├─ ZZZ_JP (Ver1.4-2.2)      ──────►  voice_mixer.py    ──►   voice-loras/
└─ ZZZ_EN                                                   emotion-samples/
```

### Comandos de Sincronização (dev-remote-01 → PC Windows)
```bash
# Testar conexão
sshpass -p 'nvidia@amd' ssh user@100.66.250.109 "dir E:\\AnimeWwise"

# Copiar personagem específico
sshpass -p 'nvidia@amd' scp -r user@100.66.250.109:"E:\\AnimeWwise\\Genshin_JP\\vo_freetalk\\vo_ayaka\\*" source_audio/vo_ayaka/

# Listar personagens disponíveis
sshpass -p 'nvidia@amd' ssh user@100.66.250.109 "dir E:\\AnimeWwise\\Genshin_JP\\vo_freetalk"
```

### Convenção de Nomes
`[game]_[char]_[gender]_[lang]`
- **Games**: `gen` (Genshin), `zzz`, `mix` (híbrido)
- **Gender**: `f` (female), `m` (male)
- **Lang**: `jp`, `en`
- **Exemplo**: `mix_ayaka_hutao_f_jp`

### ⚠️ GPU REQUIREMENT (CRÍTICO)
```
TREINAMENTO DEVE SER EXECUTADO NO gpu-node (RTX 4090)
IP: 192.168.31.200 / 100.114.21.15 (Tailscale)
SSH: ssh vmadmin@192.168.31.200

DESENVOLVIMENTO: dev-remote-01 (10.41.80.17)
FONTE DE DADOS: PC Windows (100.66.250.109)
```

### Tokenizer
Usar `checkpoints/bpe.model` (12k vocab, compatível com `gpt.pth`).

### S3 Cold Storage
```bash
# Upload após treino
mc cp trained_ckpts/mix_01_f_jp/model.pth minio/voice-loras/female/mix_01_f_jp/

# Download para produção
mc cp minio/voice-loras/female/mix_01_f_jp/model.pth ./cache/
```

### Voice Mixing (Receita)
```bash
python tools/voice_mixer.py \
    --sources gen_ayaka_f_jp gen_hutao_f_jp \
    --output mix_01_f_jp \
    --ratio 50:50
```

### Emotion Transfer (Dubbing)
```python
tts.infer(
    spk_audio_prompt='ref.wav',
    emo_audio_prompt='emotion-samples/sad/ayaka_sad.wav',  # Sentimento
    emo_alpha=0.7,
    text="Texto da linha...",
    output_path="output.wav"
)
```

### Candidatos Femininos (JP)
| Personagem | Timbre               | Path              |
| ---------- | -------------------- | ----------------- |
| Ayaka      | Elegante, Suave      | `vo_ayaka`        |
| Hu Tao     | Energética, Aguda    | `vo_hutao`        |
| Raiden     | Autoritária, Grave   | `vo_raidenshogun` |
| Yae Miko   | Sedutora, Misteriosa | `vo_yaemiko`      |
| Ganyu      | Doce, Calma          | `vo_ganyu`        |

---

## 📝 HISTÓRICO

| Data       | Mudança                                                         |
| ---------- | --------------------------------------------------------------- |
| 2026-01-07 | LoRA Factory architecture documented                            |
| 2026-01-05 | Projeto clonado e configurado                                   |
| 2026-01-08 | Arquitetura remota documentada (dev-remote-01 + PC Windows SSH) |
