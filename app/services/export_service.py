from __future__ import annotations

from io import BytesIO
import re

from openpyxl import Workbook
from openpyxl.styles import Font
from sqlalchemy.orm import Session

from app.model import (
    Event,
    EventPlayer,
    Game,
    GameParticipant,
    Player,
    ShootingRound,
    StaffUser,
    Table,
    Testament,
    TestamentTarget,
    VotingNomination,
    VotingRound,
    VotingVote,
)


def _autosize_columns(worksheet) -> None:
    for column_cells in worksheet.columns:
        values = [str(cell.value) for cell in column_cells if cell.value is not None]
        max_length = max((len(value) for value in values), default=10)
        worksheet.column_dimensions[column_cells[0].column_letter].width = min(max(max_length + 2, 12), 40)


def _add_header_row(worksheet, values: list[str]) -> None:
    worksheet.append(values)
    for cell in worksheet[worksheet.max_row]:
        cell.font = Font(bold=True)


def _safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_") or "export"


def build_event_export(db: Session, event: Event) -> tuple[str, bytes]:
    workbook = Workbook()
    summary = workbook.active
    summary.title = "Event"

    _add_header_row(summary, ["Field", "Value"])
    summary.append(["ID", event.id])
    summary.append(["Name", event.name])
    summary.append(["Date", event.date.isoformat()])
    summary.append(["Type", event.type.value])
    summary.append(["Price per game", event.price_per_game])

    registrations = (
        db.query(EventPlayer, Player)
        .join(Player, Player.id == EventPlayer.player_id)
        .filter(EventPlayer.event_id == event.id)
        .order_by(Player.nick.asc(), Player.id.asc())
        .all()
    )

    players_sheet = workbook.create_sheet("Players")
    _add_header_row(players_sheet, ["Player ID", "Nick", "Name", "Phone", "Social Link", "Games Played", "Paid Amount"])
    for registration, player in registrations:
        players_sheet.append(
            [
                player.id,
                player.nick,
                player.name,
                player.phone,
                player.social_link,
                registration.games_played,
                registration.paid_amount,
            ]
        )

    games = (
        db.query(Game, Table, StaffUser)
        .join(Table, Table.id == Game.table_id)
        .join(StaffUser, StaffUser.id == Game.host_staff_id)
        .filter(Game.event_id == event.id)
        .order_by(Game.game_number.asc(), Game.game_id.asc())
        .all()
    )

    games_sheet = workbook.create_sheet("Games")
    _add_header_row(
        games_sheet,
        ["Game ID", "Game Number", "Table", "Host", "Status", "Result", "Started At", "Finished At", "Protests"],
    )
    for game, table, host in games:
        games_sheet.append(
            [
                game.game_id,
                game.game_number,
                table.name,
                host.name,
                game.status.value,
                game.result.value if game.result else None,
                game.started_at.isoformat() if game.started_at else None,
                game.finished_at.isoformat() if game.finished_at else None,
                game.protests,
            ]
        )

    for worksheet in workbook.worksheets:
        _autosize_columns(worksheet)

    buffer = BytesIO()
    workbook.save(buffer)
    filename = f"event_{event.id}_{_safe_filename(event.name)}.xlsx"
    return filename, buffer.getvalue()


def build_game_export(db: Session, game: Game) -> tuple[str, bytes]:
    workbook = Workbook()
    summary = workbook.active
    summary.title = "Game"

    event = db.get(Event, game.event_id)
    table = db.get(Table, game.table_id)
    host = db.get(StaffUser, game.host_staff_id)

    _add_header_row(summary, ["Field", "Value"])
    summary.append(["Game ID", game.game_id])
    summary.append(["Game Number", game.game_number])
    summary.append(["Event ID", game.event_id])
    summary.append(["Event Name", event.name if event else None])
    summary.append(["Event Date", event.date.isoformat() if event else None])
    summary.append(["Table", table.name if table else None])
    summary.append(["Host", host.name if host else None])
    summary.append(["Status", game.status.value])
    summary.append(["Result", game.result.value if game.result else None])
    summary.append(["Started At", game.started_at.isoformat() if game.started_at else None])
    summary.append(["Finished At", game.finished_at.isoformat() if game.finished_at else None])
    summary.append(["Protests", game.protests])

    participants = (
        db.query(GameParticipant, Player)
        .join(Player, Player.id == GameParticipant.player_id)
        .filter(GameParticipant.game_id == game.game_id)
        .order_by(GameParticipant.seat_number.asc(), GameParticipant.id.asc())
        .all()
    )

    participants_sheet = workbook.create_sheet("Participants")
    _add_header_row(
        participants_sheet,
        ["Seat", "Player ID", "Nick", "Name", "Fouls", "Score", "Extra Score", "Role", "Alive"],
    )
    for participant, player in participants:
        participants_sheet.append(
            [
                participant.seat_number,
                player.id,
                player.nick,
                player.name,
                participant.fouls,
                participant.score,
                participant.extra_score,
                participant.role.value,
                "yes" if participant.is_alive else "no",
            ]
        )

    voting_sheet = workbook.create_sheet("Voting")
    _add_header_row(
        voting_sheet,
        [
            "Round",
            "Revote",
            "Tie",
            "Lift Applied",
            "Completed",
            "Eliminated Player ID",
            "Nominations",
            "Votes",
        ],
    )
    voting_rounds = db.query(VotingRound).filter(VotingRound.game_id == game.game_id).order_by(VotingRound.round_number.asc()).all()
    for voting_round in voting_rounds:
        nominations = (
            db.query(VotingNomination, Player)
            .join(Player, Player.id == VotingNomination.player_id)
            .filter(VotingNomination.voting_round_id == voting_round.id)
            .order_by(Player.id.asc())
            .all()
        )
        votes = (
            db.query(VotingVote, Player)
            .join(Player, Player.id == VotingVote.voter_player_id)
            .filter(VotingVote.voting_round_id == voting_round.id)
            .order_by(Player.id.asc())
            .all()
        )
        nomination_text = ", ".join(f"{player.nick}({player.id})" for _, player in nominations)
        vote_text = ", ".join(
            f"{player.nick}->{vote.target_player_id if vote.target_player_id is not None else 'X'}"
            for vote, player in votes
        )
        voting_sheet.append(
            [
                voting_round.round_number,
                voting_round.is_revote,
                voting_round.is_tie,
                voting_round.is_lift_applied,
                voting_round.is_completed,
                voting_round.eliminated_player_id,
                nomination_text,
                vote_text,
            ]
        )

    shooting_sheet = workbook.create_sheet("Shooting")
    _add_header_row(shooting_sheet, ["Round", "Shooter Player ID", "Target Player ID", "Miss"])
    shooting_rounds = (
        db.query(ShootingRound)
        .filter(ShootingRound.game_id == game.game_id)
        .order_by(ShootingRound.round_number.asc(), ShootingRound.id.asc())
        .all()
    )
    for shooting_round in shooting_rounds:
        shooting_sheet.append(
            [
                shooting_round.round_number,
                shooting_round.shooter_player_id,
                shooting_round.target_player_id,
                shooting_round.is_miss,
            ]
        )

    testament_sheet = workbook.create_sheet("Testament")
    _add_header_row(testament_sheet, ["Player ID", "Target Position", "Target Player ID"])
    testaments = (
        db.query(Testament)
        .filter(Testament.game_id == game.game_id)
        .order_by(Testament.id.asc())
        .all()
    )
    for testament in testaments:
        targets = (
            db.query(TestamentTarget)
            .filter(TestamentTarget.testament_id == testament.id)
            .order_by(TestamentTarget.position.asc(), TestamentTarget.id.asc())
            .all()
        )
        if not targets:
            testament_sheet.append([testament.player_id, None, None])
            continue
        for target in targets:
            testament_sheet.append([testament.player_id, target.position, target.target_player_id])

    for worksheet in workbook.worksheets:
        _autosize_columns(worksheet)

    buffer = BytesIO()
    workbook.save(buffer)
    filename = f"game_{game.game_id}_event_{game.event_id}.xlsx"
    return filename, buffer.getvalue()
