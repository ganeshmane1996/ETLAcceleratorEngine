from Codefile import *

with open("../Connfiguration/Configfile2.json", "r") as jsonfile:
    configure = json.load(jsonfile)
schema = data_schema(configure)
data = source(configure, schema)
result = generate_dataframe(data, configure['Operation'], configure)
destination(configure, result)
