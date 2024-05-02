from enum import Enum


class OrderBy(Enum):
    ID = "id"
    TITLE = "title"
    CREATE_TIME = "create_time"
    UPDATE_TIME = "update_time"


class Order(Enum):
    ASC = "asc"
    DESC = "desc"
