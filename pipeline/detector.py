import json
import logging

from mistralai import Mistral

logging.basicConfig(level=logging.WARNING)

PROMPT = """Extract structured data from the following user input:

{data}

Extraction Instructions:
Identify the most probable Bible reference or quoted scripture in the input text (from transcriptions, which may contain errors or variations). This could be:
- A bible verse reference (e.g. "first of Corinthians chapter ninety two verse fifty", "Mathew chapter ninety verse five hundred", "John ninety seventy", etc.)
- Ranges of verses indicated by hyphens or "to" (e.g., "first of Corinthians chapter ninety two verse fifty to seventy").
- A paraphrased or quoted scripture (e.g., "For God so loved the world...")

Additional Instructions:
- Prioritize accuracy over recall (avoid false positives).
- If a reference is ambiguous (e.g., "five nineteen" without a book), ignore it.

Normalize the result into the following fields:
- "book": Name of the book. It must be a valid name in the bible (e.g., "John", "1 Corinthians")
- "chapter": Book Chapter number as a string
- "verse": Chapter Verse number as a string

Output Format Example:
{{
  "book": "John",
  "chapter": "3",
  "verse": "16"
}}

Other Examples:
Input: "For God so loved the world..."
Output: {{
  "book": "John",
  "chapter": "3",
  "verse": "16"
}}

Input: “Mathew was given the book at 3:16am”
Output: {{}}

Input: "Nothing scriptural here"
Output: {{}}

Ensure the extracted data adheres to the specified structure and accurately represents the relevant information.
Return your response in JSON format.
"""

class DetectorAI:
    def __init__(self, *, model: str, api_key: str):
        self._model = model
        self._client = Mistral(api_key=api_key)

    async def detect_verse(self, prompt: str, data: str) -> dict:
        messages = [
            {
                'role': 'user',
                'content': prompt.format(data=data)
            }
        ]

        while True:
            try:
                response = await self._client.chat.complete_async(
                    model=self._model,
                    messages=messages,
                    response_format={
                        "type": "json_object",
                    }
                )

                break
            except Exception as err:
                logging.error("%s", str(err))
                logging.warning('Retrying to detect verse')

        content = response.choices[0].message.content
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logging.error("Failed to parse response as JSON: %s", content)
            raise


if __name__ == '__main__':
    import os
    import asyncio

    from dotenv import load_dotenv
    from fetcher import BibleFetcher

    dotenv_path = os.path.join(os.path.dirname(__file__),'..', '.env')
    load_dotenv(dotenv_path=dotenv_path)

    test_data = [
        'For God so loved the world that He gave His only begotten Son',
        'In the beginning, God created the heavens and the earth',
        'The Lord is my shepherd, I shall not want',
        'All things work together for good',
        'I can do all things through Christ who strengthens me',
        'Love is patient, love is kind',
        'Ask and it shall be given unto you',
        'Though I walk through the valley of the shadow of death',
        'John 3 16',
        'John chapter 3 verse 16',
        'Romans 8:28',
        'First Corinthians chapter 13 verse 4 to 10',
        '1Corinthians 2:3-5',
        'Revelation 21 verse 4 to verse 8',
        'Luke 6:38',
        'Today I had pizza and watched a movie',
        'I read a book called Genesis of Innovation',
        "He quoted something about love, but I can't remember it",
        'Seun was born at three sixteen am',
        'This chapter is tough, maybe the third one',
        'Chapter 4 of our math book was hard'
    ]

    fetcher = BibleFetcher()
    detector = DetectorAI(
        model=os.getenv('MISTRAL_MODEL'),
        api_key=os.getenv('MISTRAL_API_KEY')
    )

    async def main():
        for data in test_data:
            print(data)
            content = await detector.detect_verse(PROMPT, data)
            scripture = fetcher.fetch_verse(**content)
            print(scripture)

            await asyncio.sleep(2)

    asyncio.run(main())
