import asyncio
from versao1 import shorten_lyrics, remove_stopwords, STOPWORDS_PT

def test_remove_stopwords():
    text = "O gato e o rato"
    expected = "gato rato"
    assert remove_stopwords(text) == expected, f"Expected '{expected}', got '{remove_stopwords(text)}'"
    print("test_remove_stopwords passed")

def test_shorten_lyrics():
    lyrics = "Linha 1\nLinha 2\nLinha 3\nLinha 4\nLinha 5"
    # Even lines: 0 (Linha 1), 2 (Linha 3), 4 (Linha 5)
    # Stopwords to remove: none of these words are stopwords except maybe "1"? No.
    result = shorten_lyrics(lyrics)
    assert "Linha 1" in result
    assert "Linha 3" in result
    assert "Linha 5" in result
    assert "Linha 2" not in result
    assert "Linha 4" not in result
    print("test_shorten_lyrics passed")

if __name__ == "__main__":
    test_remove_stopwords()
    test_shorten_lyrics()
    print("All basic unit tests passed!")
