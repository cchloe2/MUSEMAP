"""
LLM Service — Interprète les prompts utilisateur en paramètres musicaux.

Providers supportés :
  - mock      : fallback sans clé API, règles heuristiques
  - anthropic : Claude (recommandé)
  - openai    : GPT-4o

Structure de sortie standard (toujours la même quelle que soit la source) :
{
  "genres": ["jazz", "soul"],
  "mood_keywords": ["calm", "night", "cosy"],
  "artists_hints": ["Norah Jones", "Miles Davis"],
  "energy": "low",           # low | medium | high
  "language_detected": "fr"
}
"""

import json
import re
from app.config import settings


# ════════════════════════════════════════════════════════
#  POINT D'ENTRÉE PRINCIPAL
# ════════════════════════════════════════════════════════

async def interpret_prompt(
    prompt: str,
    genres: list[str],
    mood: str,
) -> dict:
    """
    Interprète le prompt utilisateur et retourne des paramètres
    musicaux structurés pour alimenter spotify_client.

    Sélectionne automatiquement le provider configuré dans .env.
    """
    provider = settings.LLM_PROVIDER

    if provider == "anthropic" and settings.ANTHROPIC_API_KEY:
        return await _interpret_with_anthropic(prompt, genres, mood)
    elif provider == "openai" and settings.OPENAI_API_KEY:
        return await _interpret_with_openai(prompt, genres, mood)
    else:
        # Mode mock : aucune clé requise, logique heuristique
        return _interpret_with_mock(prompt, genres, mood)


# ════════════════════════════════════════════════════════
#  MOCK — Fallback sans clé API
# ════════════════════════════════════════════════════════

def _interpret_with_mock(prompt: str, genres: list[str], mood: str) -> dict:
    """
    Fallback intelligent basé sur des règles heuristiques.
    Fonctionne sans aucune clé API.
    Couvre les cas d'usage les plus fréquents du MVP.
    """
    prompt_lower = prompt.lower()

    # ── Détection de langue ──
    fr_markers = ["soirée","ambiance","calme","travail","énergie",
                  "fête","détente","concentration","nuit","matin",
                  "sport","étude","café","pluie","été","hiver"]
    lang = "fr" if any(w in prompt_lower for w in fr_markers) else "en"

    # ── Énergie ──
    high_energy = ["fête","party","workout","sport","énergie","hype",
                   "dance","dancing","run","pump","intense","hard"]
    low_energy  = ["calme","calm","sleep","détente","relax","focus",
                   "study","concentration","cosy","chill","soft","slow"]

    if any(w in prompt_lower for w in high_energy):
        energy = "high"
    elif any(w in prompt_lower for w in low_energy):
        energy = "low"
    else:
        energy = "medium"

    # ── Mood keywords enrichis depuis le prompt ──
    mood_map = {
        "relax":       ["chill", "soft", "calm", "peaceful"],
        "focus":       ["instrumental", "concentration", "deep", "flow"],
        "hype":        ["energetic", "pump", "intense", "upbeat"],
        "happy":       ["feel-good", "positive", "bright", "fun"],
        "melancholy":  ["sad", "emotional", "slow", "heartbreak"],
        "romantic":    ["love", "sensual", "intimate", "soft"],
        "workout":     ["power", "beat", "drive", "strong"],
    }
    mood_keywords = mood_map.get(mood, [mood]) if mood else []

    # Extrait des mots-clés supplémentaires du prompt (mots > 4 lettres)
    stop_words = {"pour","avec","dans","une","des","les","que","qui",
                  "the","and","for","with","that","this","playlist"}
    extra = [w for w in re.findall(r'\b\w{4,}\b', prompt_lower)
             if w not in stop_words][:4]
    mood_keywords = list(set(mood_keywords + extra))

    # ── Artistes suggérés par genre ──
    artist_hints_map = {
        "jazz":       ["Miles Davis", "Norah Jones", "Chet Baker"],
        "rock":       ["The Beatles", "Radiohead", "Arctic Monkeys"],
        "hip-hop":    ["Kendrick Lamar", "J. Cole", "Tyler the Creator"],
        "pop":        ["Dua Lipa", "Harry Styles", "Olivia Rodrigo"],
        "electronic": ["Daft Punk", "Bonobo", "Four Tet"],
        "classical":  ["Ludovico Einaudi", "Max Richter", "Debussy"],
        "r&b":        ["Frank Ocean", "SZA", "Daniel Caesar"],
        "soul":       ["Amy Winehouse", "Leon Bridges", "Lauryn Hill"],
        "indie":      ["Bon Iver", "Sufjan Stevens", "Phoebe Bridgers"],
        "reggae":     ["Bob Marley", "Damian Marley", "Chronixx"],
    }
    artist_hints = []
    for g in genres:
        artist_hints += artist_hints_map.get(g.lower(), [])

    return {
        "genres": genres,
        "mood_keywords": mood_keywords,
        "artists_hints": artist_hints[:4],
        "energy": energy,
        "language_detected": lang,
        "provider_used": "mock",
    }


# ════════════════════════════════════════════════════════
#  ANTHROPIC — Claude
# ════════════════════════════════════════════════════════

async def _interpret_with_anthropic(
    prompt: str, genres: list[str], mood: str
) -> dict:
    """
    Utilise Claude pour interpréter le prompt.
    Active dès que ANTHROPIC_API_KEY est renseignée dans .env
    et LLM_PROVIDER=anthropic.
    """
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        system = """Tu es un expert musical. Analyse le prompt utilisateur
et retourne UNIQUEMENT un JSON valide (sans markdown) avec cette structure :
{
  "genres": ["genre1", "genre2"],
  "mood_keywords": ["keyword1", "keyword2", "keyword3"],
  "artists_hints": ["Artiste1", "Artiste2"],
  "energy": "low|medium|high",
  "language_detected": "fr|en"
}
Genres disponibles sur Spotify : jazz, rock, pop, hip-hop, electronic,
classical, r&b, soul, indie, reggae, metal, country, blues, funk, latin."""

        user_msg = f"""Prompt : "{prompt}"
Genres déjà sélectionnés : {genres}
Mood sélectionné : {mood}

Enrichis et complète les paramètres musicaux."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=512,
            messages=[{"role": "user", "content": user_msg}],
            system=system,
        )

        raw = message.content[0].text.strip()
        result = json.loads(raw)
        result["provider_used"] = "anthropic"
        return result

    except Exception as e:
        print(f"[LLM] Anthropic error : {e} — fallback mock")
        return _interpret_with_mock(prompt, genres, mood)


# ════════════════════════════════════════════════════════
#  OPENAI — GPT-4o
# ════════════════════════════════════════════════════════

async def _interpret_with_openai(
    prompt: str, genres: list[str], mood: str
) -> dict:
    """
    Utilise GPT-4o pour interpréter le prompt.
    Active dès que OPENAI_API_KEY est renseignée dans .env
    et LLM_PROVIDER=openai.
    """
    try:
        import openai
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        system = """Tu es un expert musical. Analyse le prompt utilisateur
et retourne UNIQUEMENT un JSON valide (sans markdown) avec cette structure :
{
  "genres": ["genre1", "genre2"],
  "mood_keywords": ["keyword1", "keyword2", "keyword3"],
  "artists_hints": ["Artiste1", "Artiste2"],
  "energy": "low|medium|high",
  "language_detected": "fr|en"
}"""

        response = await client.chat.completions.create(
            model="gpt-4o",
            max_tokens=512,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f'Prompt: "{prompt}"\nGenres: {genres}\nMood: {mood}'},
            ],
        )

        raw = response.choices[0].message.content
        result = json.loads(raw)
        result["provider_used"] = "openai"
        return result

    except Exception as e:
        print(f"[LLM] OpenAI error : {e} — fallback mock")
        return _interpret_with_mock(prompt, genres, mood)
