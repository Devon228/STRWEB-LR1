import asyncio

import pytest

from pharmacy.concurrency import GAME_TEXTURES, fetch_texture, load_game_assets


@pytest.mark.django_db
def test_fetch_texture_returns_result():
    result = asyncio.run(fetch_texture('test.png', 1.0))
    assert result.status == 'Успешно загружено'
    assert result.name == 'test.png'
    assert result.duration_sec >= 0.1


@pytest.mark.django_db
def test_load_game_assets_faster_than_sequential():
    data = asyncio.run(load_game_assets())
    assert data['texture_count'] == len(GAME_TEXTURES)
    assert data['async_time_sec'] < data['sequential_time_sec']
    assert data['efficiency_percent'] > 0
    assert len(data['textures']) == len(GAME_TEXTURES)


def test_load_game_assets_sync_wrapper():
    data = asyncio.run(load_game_assets())
    assert data['async_time_sec'] > 0
