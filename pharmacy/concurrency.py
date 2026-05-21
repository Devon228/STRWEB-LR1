"""
Задача В (Asyncio): асинхронная подгрузка игровых текстур с сервера.
Изолированная симуляция, не связана с доменом аптеки.
"""
import asyncio
import time
from dataclasses import dataclass
from datetime import datetime

# Имя текстуры, размер в МБ (влияет на время «скачивания»)
GAME_TEXTURES = (
    ('skybox.hdr', 12.0),
    ('terrain_diffuse.png', 6.5),
    ('terrain_normal.png', 4.8),
    ('player_skin.tga', 2.1),
    ('player_anim_atlas.png', 3.4),
    ('weapon_diffuse.png', 1.8),
    ('weapon_normal.png', 1.5),
    ('muzzle_flash.png', 0.6),
    ('ui_hud.png', 1.2),
    ('particles_smoke.png', 2.0),
    ('water_caustics.png', 3.1),
    ('building_facade.jpg', 5.5),
    ('tree_billboard.png', 1.9),
    ('shadow_map_4k.raw', 8.0),
    ('ambient_occlusion.png', 4.0),
)

# Секунд ожидания на 1 МБ «текстуры»
SECONDS_PER_MB = 0.12


@dataclass
class TextureLoadResult:
    name: str
    size_mb: float
    duration_sec: float
    task_id: str
    started_at: str
    finished_at: str
    status: str


def _delay_for_size(size_mb: float) -> float:
    return round(size_mb * SECONDS_PER_MB, 3)


async def fetch_texture(texture_name: str, size_mb: float) -> TextureLoadResult:
    """Имитация скачивания одной текстуры с игрового CDN."""
    delay = _delay_for_size(size_mb)
    task = asyncio.current_task()
    task_id = task.get_name() if task else 'asyncio-task'
    started_dt = datetime.now()
    start_perf = time.perf_counter()
    await asyncio.sleep(delay)
    elapsed = time.perf_counter() - start_perf
    finished_dt = datetime.now()
    return TextureLoadResult(
        name=texture_name,
        size_mb=size_mb,
        duration_sec=round(elapsed, 3),
        task_id=task_id,
        started_at=started_dt.strftime('%d/%m/%Y %H:%M:%S'),
        finished_at=finished_dt.strftime('%d/%m/%Y %H:%M:%S'),
        status='Успешно загружено',
    )


async def load_game_assets():
    """
    Конкурентная загрузка всех текстур через asyncio.gather().
    Возвращает результаты и сравнение с гипотетической последовательной загрузкой.
    """
    sequential_estimate = sum(
        _delay_for_size(size) for _, size in GAME_TEXTURES
    )
    wall_start = time.perf_counter()
    tasks = [
        asyncio.create_task(
            fetch_texture(name, size),
            name=f'texture-{index}',
        )
        for index, (name, size) in enumerate(GAME_TEXTURES, start=1)
    ]
    results = await asyncio.gather(*tasks)
    async_elapsed = time.perf_counter() - wall_start
    if sequential_estimate > 0:
        gain_percent = round(
            (1 - async_elapsed / sequential_estimate) * 100,
            1,
        )
    else:
        gain_percent = 0.0
    return {
        'textures': results,
        'texture_count': len(results),
        'async_time_sec': round(async_elapsed, 3),
        'sequential_time_sec': round(sequential_estimate, 3),
        'efficiency_percent': gain_percent,
        'time_saved_sec': round(max(sequential_estimate - async_elapsed, 0), 3),
    }
