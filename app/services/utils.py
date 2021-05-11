# pylint: disable=no-name-in-module
import calendar
from datetime import date as Date
from typing import Optional, Sequence
from urllib.parse import urlencode, urljoin

from fastapi.requests import Request
from sqlalchemy.engine.row import Row
from pydantic import AnyHttpUrl, BaseModel, Field, PositiveInt

from app.config import settings


class YearMonth(BaseModel):
    year: Optional[PositiveInt] = Date.today().year
    month: Optional[PositiveInt] = Date.today().month


class DateRange(BaseModel):
    start: Date
    end: Date


class PageParams(BaseModel):
    offset: int = 0
    limit: int = 100


class PageMeta(BaseModel):
    total: int = Field(0)
    prv: AnyHttpUrl = Field(None)
    nxt: AnyHttpUrl = Field(None)


def get_date_range(my: YearMonth = YearMonth()) -> DateRange:
    year = my.year
    month = my.month
    last_day = calendar.monthrange(year, month)[1]
    start = Date.fromisoformat(f'{year}-{month:02}-01')
    end = Date.fromisoformat(f'{year}-{month:02}-{last_day:02}')
    return DateRange(start=start, end=end)


def populate_transaction_schema(
        result: Sequence[Row], transaction_schema: BaseModel):
    for row in result:
        transaction = transaction_schema.from_orm(row.Transaction)
        transaction.budget_name = row.budget
        transaction.category = row.category.value
        yield transaction


def generate_page_meta(request: Request, row_count: int):
    qp = {**request.query_params}
    limit = qp['limit'] = int(qp.get('limit', settings.PAGE_LIMIT))
    offset = qp['offset'] = int(qp.get('offset', settings.PAGE_OFFSET))

    prv = nxt = None
    if limit + offset < row_count:
        qp['offset'] = offset + limit
        nxt = urljoin(str(request.base_url), request.url.path) + \
            f'?{urlencode(qp)}'
    if offset > 0:
        qp['offset'] = offset - limit
        prv = urljoin(str(request.base_url), request.url.path) + \
            f'?{urlencode(qp)}'

    return PageMeta(total=row_count, prv=prv, nxt=nxt)
