from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.model import Game, EventPlayer, GamePlayer
from app.schema import GameCreate, GameResponse, GamePlayerResponse, EventAddPlayer

router = APIRouter(prefix="/games", tags=["Games"])

@router.post("", status_code=status.HTTP_201_CREATED, response_model=GameResponse)
def create_game(payload: GameCreate, db: Session = Depends(get_db)) -> Game:
    current_games_count = db.query(Game).filter(Game.event_id == payload.event_id).count()

    new_game_number = current_games_count + 1

    game = Game(
        event_id=payload.event_id, 
        table_id=payload.table_id,
        game_number=new_game_number
    )

    db.add(game)
    db.commit()
    db.refresh(game)
    return game

@router.get("/{game_id}", status_code=status.HTTP_200_OK, response_model=GameResponse)
def game_list(game_id: int, db: Session = Depends(get_db)) -> GameResponse:
    game = db.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="IGRU VVEDI NORMALNO")
    return game

# @router.put("/{game_id}", status_code=status.HTTP_200_OK, response_model=GameResponse)
# def put_event(game_id: int, payload: GameResponse, db: Session = Depends(get_db)) -> GameResponse:
#     game = db.get(Game, game_id)
#     if game is None:
#         raise HTTPException(status_code=404, detail="Game not found")
    
#     db.commit()
#     db.refresh(game)
#     return game

# 1. Нужна простая схема для входа

@router.post("/{game_id}/players", status_code=status.HTTP_201_CREATED, response_model=GamePlayerResponse)
def add_player_to_game(
    game_id: int, 
    payload: EventAddPlayer, 
    db: Session = Depends(get_db)
) -> GamePlayer:

    game = db.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    existing = db.query(GamePlayer).filter(
        GamePlayer.game_id == game_id,
        GamePlayer.player_id == payload.player_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Player already in this game")

    new_game_player = GamePlayer(
        game_id=game_id,
        player_id=payload.player_id
    )
    
    db.add(new_game_player)
    db.commit()
    db.refresh(new_game_player)
    
    return new_game_player

