from chromadb import Settings, HttpClient

client = HttpClient(host='chroma-lingwo', port=8000, settings=Settings(anonymized_telemetry=False))
themes = set()
_themes_path = 'all_themes.txt' if __import__('os').path.exists('all_themes.txt') else 'chroma/all_themes.txt'
with open(_themes_path, 'r', encoding='utf8') as file:
    lines = file.readlines()
    for s in lines:
        if len(s) != 0 and s != '\n':
            themes.add(s[s.index('.')+2:].replace('\n', ''))

collection = client.get_or_create_collection(name='themes')
collection.add(documents=list(themes), ids=list(map(str, list(range(0, len(themes))))))
exit()