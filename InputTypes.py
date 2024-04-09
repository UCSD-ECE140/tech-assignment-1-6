from pydantic import BaseModel, StringConstraints
from typing_extensions import Annotated

class NewPlayer(BaseModel):
    lobby_name: Annotated[str, StringConstraints(min_length=1, max_length=20)]
    team_name: Annotated[str, StringConstraints(min_length=1, max_length=20)]
    player_name: Annotated[str, StringConstraints(min_length=1, max_length=20)]

class Move(BaseModel):
    move: Annotated[str, StringConstraints(pattern=r'^(UP|DOWN|LEFT|RIGHT)$')]

class Start(BaseModel):
    start: Annotated[str, StringConstraints(pattern=r'^(START)$')]