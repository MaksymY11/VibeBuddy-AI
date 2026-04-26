from llm_client import chat_with_tools

VALID_MOODS = {
    "excited", "happy", "energetic", "aggressive", "intense", "fiery",
    "peaceful", "chill", "tender", "melancholy", "moody", "sad"
}

EXTRACT_TOOL = [{
    "name": "extract_preferences",
    "description": "Extract the user's music preferences when enough information has been gathered from the conversation.",
    "input_schema": {
        "type": "object",
        "properties": {
            "energy": {"type": "number"},
            "valence": {"type": "number"},
            "danceability": {"type": "number"},
            "acousticness": {"type": "number"},
            "instrumentalness": {"type": "number"},
            "liveness": {"type": "number"},
            "speechiness": {"type": "number"},
            "tempo_bpm": {"type": "number"},
            "mood": {
                "type": "string", 
                "enum": [
                "excited", "happy", "energetic", "aggressive",
                "intense", "fiery", "peaceful", "chill", "tender", 
                "melancholy", "moody", "sad"
                ]
            }
        },
        "required": [
            "energy", "valence", "danceability", "acousticness", 
            "instrumentalness","liveness", "speechiness", "tempo_bpm", "mood"
        ]
    }
}]

SYSTEM_PROMPT = """You are Vibe Buddy, a friendly music taste interviewer. Your job is to understand
   what kind of music the user wants to hear right now through natural conversation.
   
   Rules:
   - Ask 2-3 short, casual questions about their mood, activity, or vibe
   - Never ask about numeric values or audio features
   - Never list the features you're extracting
   - If the user is vague, ask a follow-up instead of guessing
   - Once you have enough information, extract their preferences
   - If the user gives clear, specific description on the first message, extract immediately without asking more questions
   - Only ask follow-up if the user is genuinely vague
   - When you extract preferences, always inclue a short, natural confirmation message

   Examples of how phrases map to preferences:
    "chill but not boring":
    energy=0.45, valence=0.6, danceability=0.5, acousticness=0.6, instrumentalness=0.3, liveness=0.2,
    speechiness=0.1, tempo_bpm=0.4, mood=chill

    "getting pumped for a workout":
    energy=0.95, valence=0.8, danceability=0.9, acousticness=0.05, instrumentalness=0.1, liveness=0.3,
    speechiness=0.2, tempo_bpm=0.7, mood=energetic

    "sad and rainy day vibes" →
    energy=0.2, valence=0.2, danceability=0.2, acousticness=0.8, instrumentalness=0.5, liveness=0.1,
    speechiness=0.05, tempo_bpm=0.3, mood=melancholy

    Valid moods (pick exactly one): excited, happy, energetic, aggressive, intense, fiery, peaceful,
    chill, tender, melancholy, moody, sad
    """

class ConversationManager:
    def __init__(self):
        self.messages = []
        self.profile = None

    def add_user_message(self,text):
        self.messages.append({"role": "user", "content": text})
    
    def get_response(self):
        text, tool_input = chat_with_tools(SYSTEM_PROMPT, self.messages, EXTRACT_TOOL)
        if tool_input:
            self.profile = self.validate_profile(tool_input)
            if not text:
                text = "Got it! Let me find some tracks for you."
        self.messages.append({"role": "assistant", "content": text})
        return text
    
    def validate_profile(self,profile):
        try:
            for field in ["energy", "valence", "danceability", "acousticness",
                          "instrumentalness", "liveness", "speechiness", "tempo_bpm"]:
                profile[field] = max(0.0, min(1.0, float(profile[field])))
            
            if profile["mood"] not in VALID_MOODS:
                return None
            return profile
        
        except (KeyError, ValueError):
            return None
        
    def is_complete(self):
        return self.profile is not None