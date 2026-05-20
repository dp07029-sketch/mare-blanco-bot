"""
Подбор размера по параметрам клиента.
"""

from config import SIZE_CHART, AVAILABLE_SIZES


def recommend_size(chest_cm: float, waist_cm: float, height_cm: float = None) -> dict:
    """
    Рекомендует размер по обхватам.
    Возвращает: {"size": "M", "fit": "well"/"loose"/"tight", "comment": "..."}
    """
    scored = []
    for entry in SIZE_CHART:
        cmin, cmax = entry["chest"]
        wmin, wmax = entry["waist"]

        # Считаем «дистанцию» — насколько параметры попадают в диапазон
        chest_mid = (cmin + cmax) / 2
        waist_mid = (wmin + wmax) / 2
        distance = abs(chest_cm - chest_mid) + abs(waist_cm - waist_mid)

        # Бонус, если попадает в диапазон
        if cmin <= chest_cm <= cmax:
            distance -= 5
        if wmin <= waist_cm <= wmax:
            distance -= 5

        scored.append((distance, entry))

    scored.sort(key=lambda x: x[0])
    best = scored[0][1]

    # Фильтруем по тому, что у вас в наличии
    if best["size"] not in AVAILABLE_SIZES:
        # Берём ближайший из доступных
        for _, entry in scored:
            if entry["size"] in AVAILABLE_SIZES:
                best = entry
                break

    # Комментарий
    cmin, cmax = best["chest"]
    if chest_cm < cmin:
        comment = "Размер будет посвободнее в груди — хороший вариант, если любите oversize."
    elif chest_cm > cmax:
        comment = "Размер будет слегка обтягивающим в груди. Рекомендуем взять на размер больше для свободной посадки."
    else:
        comment = "Идеальная посадка по груди 👌"

    return {
        "size": best["size"],
        "chest_range": best["chest"],
        "waist_range": best["waist"],
        "comment": comment,
    }
