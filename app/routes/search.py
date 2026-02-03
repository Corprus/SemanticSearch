# app/routes/search.py
from __future__ import annotations

from uuid import UUID
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from datetime import datetime

from services.search_service import SearchService
from infrastructure.deps import get_search_service

from infrastructure.auth import authenticate, CurrentUser
from services import authorization
router = APIRouter()


class SearchRequest(BaseModel):
    query_text: str
    user_id: UUID | None = None
    top_k: int = Field(default=5, ge=1, le=50)


class SearchItem(BaseModel):
    document_id: UUID
    title: str
    score: float
    rank: int


class SearchIdResponse(BaseModel):
    query_id: UUID

class SearchResultResponse(BaseModel):
    query_id: UUID
    query_status :str
    items: list[SearchItem]

class SearchHistoryResponse(BaseModel):
    query: SearchQueryResponse
    items: list[SearchResultItemResponse]


@router.post("", response_model=SearchIdResponse, summary="Отправить запрос на выполнение поиска среди документов пользователя")
def search(req: SearchRequest, search_service: SearchService = Depends(get_search_service), current_user: CurrentUser = Depends(authenticate)):
    user_id = authorization.resolve_target_user(current_user, req.user_id)
    query_id = search_service.create_query_job(user_id, req.query_text, req.top_k)    
    return SearchIdResponse(query_id=query_id)

@router.get(
    "/history",
    response_model=list[SearchHistoryResponse],
    summary="Получить историю поиска пользователя",
)
def get_search_history(
    user_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search_service: SearchService = Depends(get_search_service),
    current_user: CurrentUser = Depends(authenticate)
):
    user_id = authorization.resolve_target_user(current_user, user_id)
    history = search_service.get_history(user_id=user_id, limit=limit, offset=offset)
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


@router.get("/{query_id}/results", response_model=SearchResultResponse, summary="Получить результаты выполнения запроса")
def search_results(query_id: UUID, user_id: UUID | None = Query(default=None), search_service: SearchService = Depends(get_search_service), current_user: CurrentUser = Depends(authenticate)):
    user_id = authorization.resolve_target_user(current_user, user_id)
    if authorization.is_admin(current_user):
        user_id = None
    result = search_service.get_query_results(query_id, user_id)
    return SearchResultResponse(
        query_id=result.query_id,
        query_status=result.query.query_status,
        items=[SearchItem(document_id=i.document_id, score=i.score, rank=i.rank, title=i.document_title) for i in result.items])


class SearchResultItemResponse(BaseModel):
    document_id: UUID
    document_title: str
    score: float
    rank: int

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
    user_id: UUID | None = Query(default=None),
    search_service: SearchService = Depends(get_search_service),
    current_user: CurrentUser = Depends(authenticate)
):
    user_id = authorization.resolve_target_user(current_user, user_id)
    return [
        SearchQueryResponse(
            id=UUID(item.id), 
            user_id=UUID(item.user_id), 
            transaction_id=UUID(item.transaction_id), 
            query_text=item.query_text, 
            timestamp=item.created_at, 
            cost=str(item.cost)) 
        for item in search_service.get_query(user_id)]    

