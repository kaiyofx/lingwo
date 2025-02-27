from chromadb import Settings, HttpClient

client = HttpClient(host='chroma', port= 8000, settings=Settings(anonymized_telemetry=False))
themes = set()
with open('all_themes.txt', 'r', encoding='utf8') as file:
    lines = file.readlines()
    for s in lines:
        if len(s) != 0 and s != '\n':
            themes.add(s[s.index('.')+2:].replace('\n', ''))

collection = client.get_or_create_collection(name='themes')
collection.add(documents=list(themes), ids=list(map(str, list(range(0, len(themes))))))
exit()