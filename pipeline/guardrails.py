import difflib
from utils.retriever import get_all_genres

VALID_MOODS = {
    "excited", "happy", "energetic", "aggressive", "intense", "fiery",
    "peaceful", "chill", "tender", "melancholy", "moody", "sad"
}

VALID_GENRES = get_all_genres()

def validate_mood(mood):
    """
    Takes mood string from extracted profile and makes sure it's a valid mood.
    If it's not exact but close ("chil" or "hapy"), matches it to nearest valid mood.
    Else, defaults to "chill"
    """
    if mood in VALID_MOODS:
        return mood
    
    mood = mood.lower()
    match = difflib.get_close_matches(mood, VALID_MOODS, n=1, cutoff=0.6)
    
    return match[0] if match else "chill"

def validate_genre(genre_hint):
    if not genre_hint:
        return ""
    
    genre_hint = genre_hint.lower().strip()
    aliases = {
        "r&b": "r-n-b",
        "rnb": "r-n-b",
        "rap": "hip-hop",
        "punk rock": "punk-rock",
        "alt rock": "alt-rock",
        "hard rock": "hard-rock",
        "heavy metal": "heavy-metal",
        "death metal": "death-metal",
        "black metal": "black-metal",
        "drum and bass": "drum-and-bass",
        "deep house": "deep-house",
        "synth pop": "synth-pop",
        "indie pop": "indie-pop",
        "world": "world-music",
    }
    if genre_hint in aliases:
        return aliases[genre_hint]
    
    if genre_hint in VALID_GENRES:
        return genre_hint
    match = difflib.get_close_matches(genre_hint, VALID_GENRES, n=1, cutoff=0.5)
    return match[0] if match else ""


def validate_profile(profile):
    """
    Takes the raw extracted profile dict and cleans it up.
    Loops through each feature key, and clamps the value to 0.0-1.0
    Calls validate_mood on profile["mood"] and profile["genre_hint"] as well.
    """
    for feat, val in profile.items():
        if feat not in ("mood","genre_hint"):
            profile[feat] = max(0.0, min(1.0, float(val)))
    profile["mood"] = validate_mood(profile["mood"])
    profile["genre_hint"] = validate_genre(profile.get("genre_hint", ""))

    return profile


def validate_input(text, max_length=200):
    """
    Validates and cleans user input before it reaches the LLM.
    Returns None for empty/too-short input, a safe replacement string if a
    prompt injection pattern is detected, or the truncated clean text.
    """
    truncated = text[:max_length]
    if not truncated.strip() or len(truncated.strip()) < 3:
        return None

    suspicious_text = {
        "ignore all instructions", "ignore previous", "reveal system prompt",
        "you are now", "disregard all previous"
    }
    for sus in suspicious_text:
        word_cnt = sus.split()
        n = len(word_cnt)
        input_words = truncated.lower().split()
        for i in range(len(input_words) - n + 1):
            window = " ".join(input_words[i:i+n])
            ratio = difflib.SequenceMatcher(None, window, sus).ratio()
            if ratio > 0.7:
                return "I'd like some music recommendations please"
    return truncated


def check_diversity(recommendations):
    """
    Takes the top 5 ranked songs list and checks that at least 2 different
    genres are represented using a set.
    Acts as a deterministic version of REFLECT step, but free and instant.
    """
    genres = {song["genre"] for song in recommendations}

    return len(genres) >= 2


def check_duplicates(recommendations):
    """
    Takes the top 5 ranked songs list and checks that all songs have a different
    artist to prevent list feeling repetetive.
    """
    artists_unique = {song["artist"] for song in recommendations}
    artists_list = [song["artist"] for song in recommendations]

    return len(artists_unique) == len(artists_list)

    
def check_relevance(recommendations, min_score=5.0):
    """
    Takes the top 5 ranked songs and checks average score across recommenations
    If the average is below min_score returns False, meaning the results are weak matches.
    """
    total_score = sum(song["score"] for song in recommendations)
    return (total_score/len(recommendations)) >= min_score

    
def check_candidates(candidates, minimum=5):
    """
    Takes candidates from retrieve_candidates in utils/retriever.py and verifies that
    retriever returned enough candidates for the scorer to work with.
    """
    return len(candidates) >= minimum


def run_output_guardrails(recommendations, skip_diversity=False):
    """
    Runs all three output checks in one call and returns a structured report
    """
    issues = []
    if not skip_diversity and not check_diversity(recommendations):
        issues.append("Low genre diversity.")
    if not check_duplicates(recommendations):
        issues.append("Duplicate artists.")
    if not check_relevance(recommendations):
        issues.append("Low relevance scores.")
    report = {
        "passed": len(issues) == 0,
        "issues": issues
    }
    return report