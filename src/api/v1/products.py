from http import HTTPStatus
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from models.products import Product
from services.products_service import get_products_service, ProductService

router = APIRouter()


@router.get('/',
            response_model=List[Product],
            summary='Список продуктов',
            description='Список продуктов',
            tags=['Products'])
async def get_products(product_service: ProductService = Depends(get_products_service)) -> List[Product]:
    products = await product_service.get_all()
    if not products:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail='PRODUCT_NOT_FOUND')
    return products


@router.post('/',
             response_model=Product,
             summary='Создание продукта',
             description='Создание продукта',
             tags=['Products'])
async def create_products(
        name: str,
        product_service: ProductService = Depends(get_products_service)
) -> Product:
    check = await product_service.check_product(name)
    if check:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST,
                            detail='PRODUCT_ALREADY_EXISTS')

    product = await product_service.create(name)
    if not product:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail='PRODUCT_NOT_FOUND')
    return product


@router.get('/{uuid}',
            response_model=Product,
            summary='Продукт',
            description='Продукт',
            tags=['Products'])
async def get_product_id(
        uuid: UUID,
        product_service: ProductService = Depends(get_products_service)
) -> Product:
    product = await product_service.get_one(uuid)
    if not product:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail='PRODUCT_NOT_FOUND')
    return product


@router.put('/{uuid}',
            response_model=Product,
            summary='Изменить продукт',
            description='Изменить продукт',
            tags=['Products'])
async def edit_product_id(
        uuid: UUID,
        name: str,
        product_service: ProductService = Depends(get_products_service)
) -> Product:
    product = await product_service.edit(uuid, name)
    if not product:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail='PRODUCT_NOT_FOUND')
    return product


@router.delete('/{uuid}',
               summary='Удалить продукт',
               description='Удалить продукт',
               tags=['Products'])
async def delete_product_id(
        uuid: UUID,
        product_service: ProductService = Depends(get_products_service)
) -> None:
    product = await product_service.delete(uuid)

    return HTTPStatus.NO_CONTENT
