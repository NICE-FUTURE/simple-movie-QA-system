# -*- "coding: utf-8" -*-

fin = "genre.csv"
fout = "电影类型.csv"
with open(fin, "r", encoding="utf-8") as f:
    data = f.readlines()

with open(fout, "w", encoding="utf-8") as f:
    for line in data[1:]:
        f.write(line.strip().split(",")[-1]+",ng"+",1000\n")

fin = "movie.csv"
fout = "电影.csv"
with open(fin, "r", encoding="utf-8") as f:
    data = f.read().replace("\\\n","").split("\n")

with open(fout, "w", encoding="utf-8") as f:
    for line in data[1:]:
        try:
            f.write(line.strip().split(",")[1][1:-1]+",nm"+",1000\n")
        except IndexError as e:
            print(e)
            print(line)

fin = "person.csv"
fout = "演员.csv"
with open(fin, "r", encoding="utf-8") as f:
    data = f.readlines()

with open(fout, "w", encoding="utf-8") as f:
    for line in data[1:]:
        f.write(line.strip().split(",")[3][1:-1]+",nnt"+",1000\n")
