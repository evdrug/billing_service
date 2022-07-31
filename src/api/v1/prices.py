from enum import Enum
from http import HTTPStatus
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException

from models.prices import Price, TypeRecurring, TypePrice
from services.prices_service import get_price_service, PriceService
from grpc_auth_client.dependencies import get_permissions

router = APIRouter()


@router.get('/product/{uuid}',
            response_model=List[Price],
            summary='Список цен у продукта',
            description='Список цен у продукта',
            tags=['Prices'])
async def get_prices(
        uuid: UUID,
        price_service: PriceService = Depends(get_price_service)
) -> List[Price]:
    prices = await price_service.get_all_in_product(uuid)
    if not prices:
        return []
    return prices


class Interval(Enum):
    month = 'month'
    year = 'year'


@router.post('/',
             response_model=Price,
             summary='Создание Price',
             description='Создание Price',
             tags=['Prices'])
async def create_price(
        name: str,
        product_id: UUID,
        permission_id: int,
        unit_amount: int,
        currency: str,
        type_price: TypePrice = Query(...),
        interval_count: Optional[int] = Query(None, ge=1, le=12),
        interval: Optional[Interval] = Query(None),
        using_type: Optional[TypeRecurring] = Query(None),
        price_service: PriceService = Depends(get_price_service)
) -> Price:
    # Todo check interval and interval_count

    if type_price == TypePrice.recurring and not any([interval_count, interval, using_type]):
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST,
                            detail='Not Data Recurring')

    price = await price_service.create(
        name,
        product_id,
        permission_id,
        unit_amount, currency,
        interval,
        interval_count,
        type_price,
        using_type
    )
    if not price:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail='PRICE_NOT_FOUND')
    return price


@router.get('/{uuid}',
            response_model=Price,
            summary='Price',
            description='Price',
            tags=['Prices'])
async def get_price_id(
        uuid: UUID,
        price_service: PriceService = Depends(get_price_service),
        permissions=Depends(get_permissions)
) -> Price:
    price = await price_service.get_one(uuid)
    if not price:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail='PRICE_NOT_FOUND')
    return price

# TODO надо определиться, будем ли что-то править для прайса

# @router.put('/{uuid}',
#             response_model=Price,
#             summary='Изменить price',
#             description='Изменить price',
#             tags=['Prices'])
# async def edit_price_id(
#         uuid: UUID,
#         name: str,
#         price_service: PriceService = Depends(get_price_service)
# ) -> Price:
#     price = await price_service.edit(uuid, name)
#     if not price:
#         raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
#                             detail='PRICE_NOT_FOUND')
#     return price


@router.delete('/{uuid}',
               summary='Удалить Price',
               description='Удалить Price',
               tags=['Prices'])
async def delete_product_id(
        uuid: UUID,
        price_service: PriceService = Depends(get_price_service)
) -> None:
    price = await price_service.delete(uuid)

    return HTTPStatus.NO_CONTENT
