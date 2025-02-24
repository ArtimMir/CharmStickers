import requests
import json
import time
import os
import urllib.parse

# Путь к файлу кэша
CACHE_FILE = "steam_price_cache.json"
# Путь к HTML-файлу
HTML_FILE = "price_comparison.html"

# Функция для загрузки кэша из файла
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Функция для сохранения кэша в файл
def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=4)

# Функция для нормализации названия предмета
def normalize_item_name(item_name):
    normalized = " ".join(item_name.split())  # Убираем двойные пробелы
    encoded = urllib.parse.quote(normalized)
    return encoded

# Функция для получения цены предмета из Steam через API
def get_steam_price(item_name, cache, appid=730, currency=1):
    if item_name in cache:
        print(f"Цена для {item_name} найдена в кэше: {cache[item_name]}")
        return cache[item_name]
    
    encoded_name = normalize_item_name(item_name)
    url = f"https://steamcommunity.com/market/priceoverview/?appid={appid}&currency={currency}&market_hash_name={encoded_name}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        print(f"Исходное название: {item_name}")
        print(f"Закодированное название: {encoded_name}")
        print(f"Полный URL: {url}")
        response = requests.get(url, headers=headers)
        print(f"HTTP статус: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Ответ Steam API для {item_name}: {data}")
            if data and data.get("success") and "lowest_price" in data:
                price = float(data["lowest_price"].replace("$", "").replace(",", "."))
                cache[item_name] = price
                save_cache(cache)
                print(f"Получена цена Steam для {item_name}: {price}")
                return price
            else:
                print(f"Steam API не вернул цену для {item_name}: {data}")
                return None
        else:
            print(f"Ошибка HTTP {response.status_code} для {item_name}: {response.text}")
            return None
    except Exception as e:
        print(f"Ошибка при запросе Steam для {item_name}: {e}")
        return None

# Функция для получения списка предметов и цен с swap.gg через API
def get_swap_items():
    url = "https://api.swap.gg/v2/trade/inventory/bot/730"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        if data.get("status") == "OK" and "result" in data:
            items = []
            for item in data["result"]:
                name = item["n"]
                price = item["p"] / 100
                items.append({"name": name, "swap_price": price})
                print(f"Получен предмет с swap.gg: {name}, цена: {price}")
            return items
        else:
            print("Ошибка в структуре ответа swap.gg:", data)
            return []
    except Exception as e:
        print(f"Ошибка при запросе к swap.gg API: {e}")
        return []

# Функция для создания начального HTML с сортировкой
def init_html():
    html_start = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Сравнение цен Steam и Swap.gg</title>
        <style>
            table {
                width: 80%;
                margin: 20px auto;
                border-collapse: collapse;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: center;
            }
            th {
                background-color: #f2f2f2;
                cursor: pointer;
            }
            th:hover {
                background-color: #ddd;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
        </style>
        <script>
            function sortTable() {
                var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
                table = document.querySelector("table");
                switching = true;
                dir = "asc"; // Направление сортировки: по возрастанию
                while (switching) {
                    switching = false;
                    rows = table.rows;
                    for (i = 1; i < (rows.length - 1); i++) {
                        shouldSwitch = false;
                        x = rows[i].getElementsByTagName("td")[3]; // Последний столбец (Процент выгоды)
                        y = rows[i + 1].getElementsByTagName("td")[3];
                        var xValue = parseFloat(x.innerHTML);
                        var yValue = parseFloat(y.innerHTML);
                        if (dir == "asc") {
                            if (xValue > yValue) {
                                shouldSwitch = true;
                                break;
                            }
                        } else if (dir == "desc") {
                            if (xValue < yValue) {
                                shouldSwitch = true;
                                break;
                            }
                        }
                    }
                    if (shouldSwitch) {
                        rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                        switching = true;
                        switchcount++;
                    } else {
                        if (switchcount == 0 && dir == "asc") {
                            dir = "desc";
                            switching = true;
                        }
                    }
                }
            }
        </script>
    </head>
    <body>
        <table>
            <tr>
                <th>Название предмета</th>
                <th>Цена в Steam ($)</th>
                <th>Цена на Swap.gg ($)</th>
                <th onclick="sortTable()">Процент выгоды (%)</th>
            </tr>
    """
    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html_start)
    print(f"HTML-файл инициализирован: {HTML_FILE}")

# Функция для добавления строки в HTML
def append_html_row(item):
    steam_price = item.get("steam_price")
    swap_price = item.get("swap_price")
    if steam_price is not None and swap_price is not None:
        profit_percent = ((steam_price - swap_price) / steam_price) * 100 if steam_price > 0 else 0
        row = f"""
            <tr>
                <td>{item['name']}</td>
                <td>{steam_price:.2f}</td>
                <td>{swap_price:.2f}</td>
                <td>{profit_percent:.2f}</td>
            </tr>
        """
        with open(HTML_FILE, "a", encoding="utf-8") as f:
            f.write(row)
        print(f"Добавлена строка для {item['name']}: Steam={steam_price}, Swap={swap_price}, Выгода={profit_percent:.2f}%")
    else:
        print(f"Пропущен предмет {item['name']}: Steam={steam_price}, Swap={swap_price}")

# Функция для завершения HTML
def finish_html():
    html_end = """
        </table>
    </body>
    </html>
    """
    with open(HTML_FILE, "a", encoding="utf-8") as f:
        f.write(html_end)
    print("HTML-файл завершен")

# Основная функция
def main():
    steam_cache = load_cache()
    print(f"Загружен кэш с {len(steam_cache)} предметами")
    
    print("Парсинг данных с swap.gg через API...")
    swap_items = get_swap_items()
    
    if not swap_items:
        print("Не удалось получить данные с swap.gg. Проверьте API или доступ.")
        return
    
    print(f"Найдено {len(swap_items)} предметов на swap.gg.")
    
    init_html()
    
    print("Получение цен из Steam и формирование таблицы...")
    processed_items = 0
    for item in swap_items:
        item["steam_price"] = get_steam_price(item["name"], steam_cache)
        append_html_row(item)
        if item["steam_price"] is not None:
            processed_items += 1
        if item["steam_price"] is None and item["name"] not in steam_cache:
            time.sleep(1)
    
    finish_html()
    
    print(f"Успешно обработано {processed_items} предметов.")
    print(f"Таблица сохранена в файл {HTML_FILE}")

if __name__ == "__main__":
    main()