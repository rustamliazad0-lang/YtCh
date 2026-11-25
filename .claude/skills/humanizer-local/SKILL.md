---
name: humanizer-local
description: Rewrite an AI-written draft (email, essay, report, post; English or Chinese) so it reads like a person wrote it, using the local humanizer model (github.com/sgaofen/humanizer-local-model). Use when the user asks to humanize, de-AI, or rephrase a draft and has the humanizer app, the `hz` command, or a llama-server running on their own computer.
---

# humanizer (local rewrite)

Rewrites one draft so it sounds like a person wrote it. It keeps numbers, units, dates, names and quotes, and it adds nothing. The model runs on the user's own computer. It cannot run in this cloud session.

## Before you start

1. Ask where the model runs. Options:
   - The Humanizer app (Mac with Apple silicon or Windows x64): https://github.com/sgaofen/humanizer-local-model/releases/latest
   - `hz` command-line tool, for long Markdown or `.docx` files
   - llama-server with the GGUF file, for scripts
2. If the user has none of these, say so and stop. Do not invent a rewrite.
3. Check the context: if the text is for coursework or an application, remind the user to check the university's rules on AI use first. Do not help hide AI authorship where the rules forbid it.

## Using `hz` (user's computer)

```bash
pipx install git+https://github.com/sgaofen/humanizer-local-model
hz draft.txt                          # prints the rewrite
hz paper.md -o paper.out.md           # long Markdown: structure kept
hz report.docx -o report.out.docx     # needs: pipx inject humanize-model python-docx
hz paper.md --json                    # stats per piece, for scripts
```

`hz` uses the running app or a llama-server. It lists pieces where a number from the draft is missing or a new number appeared.

## Using llama-server (user's computer)

1. Install llama.cpp (build b11335 or newer).
2. Start the server with a model file from https://huggingface.co/jialinyyzz/humanizer. Use Q8_0 with 32 GB RAM, Q6_K with 16 GB, and smaller files for less memory.
3. Call `/completion`, not the chat endpoint. The model is a text-completion model. Get the exact prompt from `prompt_format.json` in the same Hugging Face repo.
4. Sampling: temperature 1.0, top_p 0.95, top_k 0, min_p 0, repeat_penalty 1.0.

## Checks before returning a result

- Read the whole rewrite. Names and the meaning of sentences are not checked automatically.
- Compare every number, date and name with the draft yourself.
- If the rewrite is in Chinese for an English draft, run it again.
- Do not promise that any AI detector will pass the text.

## Limits

- No cloud run. Do not try to load the model here.
- Only the user's computer can run it. Phone-only sessions cannot use this skill.
