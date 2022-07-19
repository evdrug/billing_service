import orjson
from pydantic import BaseModel

from utils.json_dumps import orjson_dumps


class OrjsonBase(BaseModel):
    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps