import json

class BibleFetcher:
    def __init__(self, translation: str = "NKJV"):
        json_path = translation.lower() + '.json'
        with open(json_path, 'r', encoding='utf-8') as file:
            self._bible_data = json.load(file)

        self.translation = translation

    def fetch_verse(self, book: str, chapter: str, verse: str):
        verse = verse.strip()
        chapter = chapter.strip()
        book = book.strip().lower()

        if not (book and chapter and verse):
            return None

        try:
            end_verse = None
            verses = verse.split('-')
            start_verse = verses[0]
            if len(verses) > 2:
                raise ValueError

            if len(verses) == 2:
                end_verse = verses[1]

            scripture = f"{book.capitalize()} {chapter}:{verse}\n"
            book_chapter = self._bible_data[book][chapter]
            if end_verse:
                for i in range(int(start_verse), int(end_verse) + 1):
                    scripture = scripture + f"{i}. {book_chapter[str(i)]}\n"
            else:
                scripture = scripture + f"{start_verse}. {book_chapter[start_verse]}\n"

            return scripture
        except (KeyError, IndexError, ValueError):
            return None
