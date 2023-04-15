from Codefile import *

with open("../Connfiguration/Configfile3.json", "r") as jsonfile:
    configure = json.load(jsonfile)
schema = data_schema(configure)
data = source(configure, schema)
result = generate_dataframe(data, configure['Operation'], configure)
result.show()
destination(configure, result)
print("end")
