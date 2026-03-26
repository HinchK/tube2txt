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
                "Adhere to 'The Elements of Style' (1918): omit needless words, "
                "be specific, concrete, and definite."
            ),
            'notes': (
                "Create detailed study notes from this transcript. "
                "Adhere strictly to the principles of 'The Elements of Style' (1918): "
                "Be clear, concise, and use the active voice. Omit needless words. "
                "Include key takeaways, definitions of complex terms, and a summary for each major section. "
                "Use timestamps in brackets [HH:MM:SS]."
            ),
            'recipe': (
                "Extract recipes, ingredients, and cooking steps from this transcript. "
                "Follow 'The Elements of Style' (1918): use the active voice for instructions, "
                "be specific and definite, and omit needless words. "
                "Format them clearly in markdown with timestamps [HH:MM:SS]."
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
Based on the following video outline, determine which of these three modes is most appropriate for a deep-dive:
1. 'recipe' (if it's a cooking video or contains a recipe)
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
