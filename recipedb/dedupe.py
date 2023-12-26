import json

recipe_ids = set()
with open("recipedb.ndjson", "r") as fp, open("recipdb.dedupe.ndjson", "w") as wfp:
    while line := fp.readline():
        recipe = json.loads(line)
        _id = recipe["Recipe_id"]
        if _id not in recipe_ids:
            recipe_ids.add(_id)
            wfp.write(line)

print(len(recipe_ids))
