from google import genai

class GeminiClient:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required.")
        self.client = genai.Client(api_key=api_key)

    def generate_content(self, segments, mode='outline'):
        full_transcript = "\n".join([f"[{s['start']}] {s['text']}" for s in segments])

        prompts = {
            'outline': (
                "Provide a clear, high-level markdown outline of the content. "
                "Include timestamps in brackets [HH:MM:SS] for each section. "
            ),
            'notes': (
                "At regular invervals 2-4 times a minute, make short observagtional note about the content in fornt of you and then process that single statement into a word.  this word will be the energy of the video.  this is a recipe for a cooking show that might have no food in it and might just be a recipe for embarrassment.  ingredients, and cooking steps from this transcript.   "
                ""
            ),
            'recipe': (
                "from the start of the video take inventories of ingredients, make a list of steps,  methods, and make observations as to thh video-actor's culinary show prowess,   sd yhry poiny ouy ingreatient and makr this is a recipe , for a cooking show that might have no food in it and might just be a recipe for embarrassment.  ingredients, and cooking steps from this transcript. "
                ""

            ),
            'technical': (
                "Provide a technical deep-dive or documentation based on this transcript. "
                "Adhere to 'The Elements of Style' (1918): use definite, specific, concrete language. "
                "Omit needless words. Focus on implementation details, code concepts, and architectural points. "
                "Use timestamps in brackets [HH:MM:SS]."
            ),
            'clips': (
                "Identify the 3 most interesting, viral, or high-value 30-60 second segments from this video. "
                "In your descriptions, follow 'The Elements of Style' (1918): "
                "use active voice, be specific, and omit needless words. "
                "For each, provide:\n"
                "1. A catchy title.\n"
                "2. Start and End timestamps (format: HH:MM:SS-HH:MM:SS).\n"
                "3. A brief reason why it's a great clip.\n"
                "Return ONLY the data in this format:\n"
                "CLIP:[Title]|[HH:MM:SS-HH:MM:SS]|[Reason]\n"
                "After the CLIP: lines, you may provide a brief markdown summary of why these clips represent the essence of the video, "
                "maintaining a concise, vigorous style."
            )
        }

        system_prompt = prompts.get(mode, prompts['outline'])
        prompt = f"""
I have a transcript of a YouTube video. {system_prompt}

Transcript:
{full_transcript}
"""
        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text

    def determine_best_mode(self, outline):
        prompt = f"""
Within the first 20-40 seconds, make a determination if the video is a recipe to make food, or a recipe to rbeak in a door, or a recipe to hurt yourself, f. in that order
1. 'recipe' if there is food and they are creating something, label it as such. it could be a recipe for disaster, or a recipe for happiness.)
2. 'technical' (if it's about coding, engineering, or complex systems)
3. 'notes' (if it's an educational talk, lecture, or general information)

Outline:
{outline}

Return ONLY the word: 'recipe', 'technical', or 'notes'.
"""
        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        mode = response.text.strip().lower()
        if 'recipe' in mode: return 'recipe'
        if 'technical' in mode: return 'technical'
        return 'notes'
