# story.py
# Детeрминированный генератор сюжетной карты на 500 узлов.
# Импортируйте: from story import story
# Получите словарь: story[1], story[2], ..., story[500]
# В узлах 1..450 — игровые сцены с полем "choices" (варианты a..e).
# В узлах 451..500 — терминальные исходы с полями:
#    - result: "win" или "lose"
#    - explanation: объяснение, почему такой исход
# Всё детерминировано — без рандома.

from typing import Dict


def title_for(i: int) -> str:
    moods = [
        "Холодный неон и редкий дождь.",
        "Тёплая лампа в спальне инженера.",
        "Звук вентиляторов и шёпот серверов.",
        "Пыльный склад и запах машинного масла.",
        "Шумный порт и крик чаек."
    ]
    return moods[i % len(moods)]


def main_character() -> str:
    return "Астра"  # имя главного героя (можно поменять)


def other_chars(i: int) -> str:
    names = ["Мира (инженер)", "Хокинс (директор)", "Ли (аналитик)", "Кот (информатор)", "Наир (кинолог)"]
    return names[i % len(names)]


def scene_text(i: int) -> str:
    base = f"{title_for(i)} {main_character()} на шаге {i}."
    patterns = [
        f"{base} В городе появились слухи о перезапусках андроидов — {other_chars(i)} даёт новую зацепку.",
        f"{base} Вы обнаружили странный лог и почувствовали запах бензина — улика ведёт дальше.",
        f"{base} Ночной контакт сообщил координаты. Решение — за вами.",
        f"{base} В комнате инженера — лужа масла и записка с обрывком шифра.",
        f"{base} Система слежения зафиксировала перемещение грузовика в порт."
    ]
    return patterns[i % len(patterns)]


def choice_text(i:int, idx:int) -> str:
    verbs = [
        "Пойти на шум",
        "Разобраться тихо",
        "Сообщить в штаб",
        "Проверить по базе",
        "Рискнуть и ворваться"
    ]
    extras = [
        "— осторожно, без шума.",
        "— собрав как можно больше доказательств.",
        "— прежде чем действовать.",
        "— найти связь с CyberLife.",
        "— дать волю инстинкту."
    ]
    return f"{verbs[idx % len(verbs)]} {extras[idx % len(extras)]}"


def next_target(i:int, choice_idx:int) -> int:
    # Детерминированные переходы: ранние шаги ведут дальше по цепочке,
    # ближе к концу — к терминалам 451..500
    if i >= 430:
        base = 451 + ((i * (choice_idx+1)) % 50)
        return base
    else:
        offset = ((i * (choice_idx + 2)) % 6) + 1
        nxt = i + offset
        if nxt > 450:
            nxt = 451 + ((i + choice_idx) % 50)
        return nxt


def terminal_explanation(idx: int) -> Dict[str,str]:
    lose_reasons = [
        "Вы проиграли, потому что упустили критическое доказательство.",
        "Поражение: подкрепление опоздало, операция скомпрометирована.",
        "Поражение: вас выследили и захватили.",
        "Поражение: данные были уничтожены до публикации.",
        "Поражение: вы действовали поспешно и попали в ловушку."
    ]
    win_reasons = [
        "Победа: вы разоблачили заговор и спасли инженера.",
        "Победа: саботаж прошёл успешно — перезапуски сорваны.",
        "Победа: журналисты подняли проблему и общество отреагировало.",
        "Победа: вы получили ключевой модуль и передали его экспертам.",
        "Победа: координатор выдан, суд вынес решение против CyberLife."
    ]
    if (idx % 4) in (0,1):
        return {"result":"lose", "explanation": lose_reasons[idx % len(lose_reasons)]}
    else:
        return {"result":"win", "explanation": win_reasons[idx % len(win_reasons)]}


def build_story() -> Dict[int, dict]:
    story: Dict[int, dict] = {}

    # 1..450 — игровые узлы
    for i in range(1, 451):
        n_choices = (i % 4) + 2  # от 2 до 5
        choices = {}
        for j in range(n_choices):
            key = chr(ord('a') + j)
            choices[key] = {
                "text": choice_text(i, j),
                "next": next_target(i, j)
            }
        story[i] = {
            "text": scene_text(i),
            "choices": choices
        }

    # 451..500 — терминалы (win/lose) с объяснением
    for idx in range(451, 501):
        info = terminal_explanation(idx)
        story[idx] = {
            "text": ("Финал (успех)" if info["result"]=="win" else "Финал (поражение)") + f" — узел {idx}. {other_chars(idx)} присутствует в сцене.",
            "result": info["result"],
            "explanation": info["explanation"]
        }

    return story


# Готовый словарь для импорта
story = build_story()

# Небольшая справка при запуске как скрипта
if __name__ == '__main__':
    import json
    print('story nodes:', len(story))
    # покажем 3 первых узла
    print(json.dumps({k: story[k] for k in range(1,4)}, ensure_ascii=False, indent=2))
