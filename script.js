let maxPrice = 0;
let maxStikov = 0;
let newStiks = 0;
let badStiks = 0;
let stickPrices = JSON.parse(localStorage.getItem('stickPrices')) || [];

async function getStickerPrice(itemNameMain) {
    let price = 0;
    const filterStick = stickPrices.filter(entry => entry.success === itemNameMain);
    
    if (filterStick.length > 0) {
        price = parseFloat(filterStick[0].lowest_price.replace('$', '').replace(' USD', ''));
        console.log(`Цена из localStorage для ${itemNameMain}: ${price}`);
    } else {
        const itemName = itemNameMain.replace('|', '%7C').replace(' ', '%20');
        const url = `https://steamcommunity.com/market/priceoverview/?country=RU¤cy=1&appid=730&market_hash_name=Sticker%20%7C%20${itemName}`;
        
        try {
            const response = await fetch(url, { credentials: 'include' });
            if (response.ok) {
                const data = await response.json();
                price = data.lowest_price ? parseFloat(data.lowest_price.replace('$', '').replace(' USD', '')) : 0;
                data.success = itemNameMain;
                stickPrices.push(data);
                localStorage.setItem('stickPrices', JSON.stringify(stickPrices));
                newStiks++;
                console.log(`Новая цена для ${itemNameMain}: ${price}`);
                await new Promise(resolve => setTimeout(resolve, 5000));
            } else {
                badStiks++;
                console.error(`Ошибка ${response.status} для ${itemNameMain}`);
            }
        } catch (error) {
            console.error('Ошибка запроса:', error);
            badStiks++;
        }
    }
    return price;
}

async function fetchData() {
    maxPrice = parseFloat(document.getElementById('maxPrice').value) || 10; // Значение по умолчанию
    newStiks = 0;
    badStiks = 0;
    maxStikov = 0;

    try {
        const response = await fetch('https://api.swap.gg/v2/trade/inventory/bot/730');
        if (!response.ok) {
            alert('Нет доступа к swap.gg');
            setTimeout(fetchData, 30000);
            return;
        }

        const data = await response.json();
        console.log('Данные от swap.gg:', data);
        const results = [];
        let gvIndex = 0;

        for (const item of data.result) {
            if (item.n.includes('Souvenir')) continue;

            if (item.m && item.m['5']) {
                let skokStikov = 0;
                let sumStikov = 0;
                const stickNames = [];
                let xField = '';
                const pistolPrice = item.p / 100;

                // Убери проверку для теста
                // if (pistolPrice > maxPrice) continue;
                if (pistolPrice < 0.5) xField = 'X';

                for (const subItem of item.m['5']) {
                    if (subItem.name && subItem.wear === 0) {
                        gvIndex++;
                        skokStikov++;
                        stickNames.push(subItem.name);
                        const price = await getStickerPrice(subItem.name);
                        sumStikov += price;
                    }
                }

                if (skokStikov > maxStikov) maxStikov = skokStikov;
                results.push([item.n, pistolPrice, xField, stickNames.join(', '), sumStikov]);
            }
        }

        console.log('Результаты:', results);
        results.sort((a, b) => b[4] - a[4]);

        const tableBody = document.getElementById('tableBody');
        tableBody.innerHTML = '';
        results.forEach(row => {
            const tr = document.createElement('tr');
            row.forEach(cell => {
                const td = document.createElement('td');
                td.textContent = cell;
                tr.appendChild(td);
            });
            tableBody.appendChild(tr);
        });

        document.getElementById('badStickers').textContent = badStiks;
        document.getElementById('newStickers').textContent = newStiks;
        document.getElementById('maxStickers').textContent = maxStikov;
    } catch (error) {
        console.error('Ошибка в fetchData:', error);
    }

    setTimeout(fetchData, 30000);
}