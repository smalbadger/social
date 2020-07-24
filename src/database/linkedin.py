import sqlalchemy as db
from pprint import pprint

if __name__ == "__main__":
    engine = db.create_engine('mysql+pymysql://root:raspberry1!@k7aim.net:3306/linkedin', pool_recycle=3600)
    connection = engine.connect()
    metadata = db.MetaData()

    # reflect db schema to MetaData
    metadata.reflect(bind=engine)
    print(metadata.tables)

    # contacts = db.Table('Contacts', metadata, autoload=True, autoload_with=engine)
    #
    # query = db.select([contacts])
    # resultProxy = connection.execute(query)
    #
    # done = False
    # while not done:
    #     partial_results = resultProxy.fetchmany(50)
    #     if partial_results == []:
    #         done = True
    #     else:
    #         pprint(partial_results)
