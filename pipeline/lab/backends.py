class ExperimentBackend:
    def __init__(self, conf):
        self.con = None

    def get(id):
        # fetch model with id or ids if it's a list
        pass

    def get_k(self, subset, key, k, descending=True):
        # get k models by filtering and sorting
        pass

    def store(record):
        # store record or records if it's a list
        pass


class MongoBackend:
    def __init__(self, conf):
        from pymongo import MongoClient

        client = MongoClient(conf['uri'])
        db = conf['db']
        collection = conf['collection']
        self.con = client[db][collection]

    def save(self, dicts):
        self.con.insert_many(dicts)

    def update(self, dicts):
        from bson.objectid import ObjectId

        for d in dicts:
            self.con.replace_one({'_id': ObjectId(d['_id'])}, d)

    def get(self, **kwargs):
        from bson.objectid import ObjectId
        from pipeline.util import _can_iterate

        # process ids in case _id is on kwargs
        if '_id' in kwargs:
            value = kwargs['_id']
            if _can_iterate(value):
                kwargs['_id'] = [ObjectId(an_id) for an_id in value]
            else:
                kwargs['_id'] = ObjectId(value)

        def to_mongo(value):
            if _can_iterate(value):
                return {'$in': value}
            else:
                return value

        for k in kwargs:
            kwargs[k] = to_mongo(kwargs[k])

        results = list(self.con.find(kwargs))
        return results


class TinyDBBackend:
    def __init__(self, conf):
        from tinydb import TinyDB

        self.con = TinyDB(conf['path'])

    def save(self, dicts):
        self._cast_unserializable(dicts)
        self.con.insert_multiple(dicts)

    def update(self, dicts):
        self._cast_unserializable(dicts)
        for d in dicts:
            self.con.update(d, eid=[d.eid])

    def get(self, **kwargs):
        raise Exception('Not implemented')

    @staticmethod
    def _cast_unserializable(dicts):
        # tinydb cannot serialize some objects to json
        # cast them before saving
        import datetime
        for d in dicts:
            for k, v in d.items():
                if isinstance(v, datetime.datetime):
                    d[k] = v.strftime("%Y-%m-%d %H:%M:%S")
