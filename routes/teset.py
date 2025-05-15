id = "<10.52.32.214>1.0"
if "<" in id:
    id = id.split("<")[1]
    id = id.split(">")[0]
    print(id)