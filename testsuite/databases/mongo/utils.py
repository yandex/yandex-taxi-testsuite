import pymongo


SORT_STR_TO_PYMONGO = {
    'ascending': pymongo.ASCENDING,
    'descending': pymongo.DESCENDING,
    '2d': pymongo.GEO2D,
    '2dsphere': pymongo.GEOSPHERE,
    'hashed': pymongo.HASHED,
    'text': pymongo.TEXT,
}
