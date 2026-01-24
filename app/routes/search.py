# app/routes/search.py
from __future__ import annotations

from uuid import UUID
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from services.search_service import SearchService
from infrastructure.deps import get_search_service
from datetime import datetime
router = APIRouter()


class SearchRequest(BaseModel):
    user_id: UUID
    query_text: str
    top_k: int = Field(default=5, ge=1, le=50)


class SearchItem(BaseModel):
    document_id: UUID
    score: float
    rank: int


class SearchResponse(BaseModel):
    query_id: UUID
    items: list[SearchItem]


@router.post("", response_model=SearchResponse, summary="Выполнить поиск среди документов пользователя")
def search(req: SearchRequest, search_service: SearchService = Depends(get_search_service)):
    results = search_service.search(req.user_id, req.query_text, req.top_k)
    return SearchResponse(
        query_id=results.query_id,
        items=[SearchItem(document_id=i.document_id, score=i.score, rank=i.rank) for i in results.items])

class SearchResultItemResponse(BaseModel):
    document_id: UUID
    document_title: str
    score: float
    rank: int


class SearchHistoryResponse(BaseModel):
    query: SearchQueryResponse
    items: list[SearchResultItemResponse]


class SearchQueryResponse(BaseModel):
    id: UUID
    user_id: UUID
    transaction_id: UUID
    query_text: str
    cost: str
    timestamp: datetime

@router.get(
    "/{query_id}",
    response_model=list[SearchQueryResponse],
    summary="Получить запрос пользователя по id",
)
def get_search_query(
    user_id: UUID,
    search_service: SearchService = Depends(get_search_service),
):
    return [
        SearchQueryResponse(
            id=UUID(item.id), 
            user_id=UUID(item.user_id), 
            transaction_id=UUID(item.transaction_id), 
            query_text=item.query_text, 
            timestamp=item.created_at, 
            cost=str(item.cost)) 
        for item in search_service.get_query(user_id)] 
    

@router.get(
    "/history/{user_id}",
    response_model=list[SearchHistoryResponse],
    summary="Получить историю поиска пользователя",
)
def get_search_history(
    user_id: UUID,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search_svc: SearchService = Depends(get_search_service),
):
    history = search_svc.get_history(user_id=user_id, limit=limit, offset=offset)

    return [
        SearchHistoryResponse(
            query = SearchQueryResponse(
                id=UUID(item.query.id), 
                user_id=UUID(item.query.user_id), 
                transaction_id=UUID(item.query.transaction_id), 
                query_text=item.query.query_text, 
                timestamp=item.query.created_at, 
                cost=str(item.query.cost)),
            items=[
                SearchResultItemResponse(
                    document_id=i.document_id,
                    document_title=i.document_title,
                    score=i.score,
                    rank=i.rank,
                )
                for i in item.items
            ],
        )
        for item in history
    ]
