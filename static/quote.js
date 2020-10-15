const symbols = new Set();

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('form').onsubmit = () => {
        // If symbol is not a duplicate
        if (!symbols.has(document.getElementById('symbol').value)) {
            // Initialize new request
            const request = new XMLHttpRequest();
            const newSymbol = document.getElementById('symbol').value;
            symbols.add(newSymbol);
            request.open('POST', '/stocks/quote', true);
        
            // Callback function for when request completes
            request.onload = () => {
                
                // Extract JSON data from request
                try {
                    const data = JSON.parse(request.responseText);
                    // Update the result div
                    if (data.success) {
                        const tBody = document.getElementById('tBody');
                        tBody.innerHTML = '';
                        for (let i = 0; i < data.stocks.length; i++) {
                            let row = tBody.insertRow(0);
                            for (let c=0; c < 3; c++) {
                                row.insertCell(c);
                            }
                            row.cells[0].innerHTML = data.stocks[i].name;
                            row.cells[1].innerHTML = data.stocks[i].price;
                            row.cells[2].innerHTML = data.stocks[i].symbol;
                        }
                        console.log('Form triggered stock update successful');
                    } else {
                        symbols.delete(newSymbol);
                        console.log('Form triggered stock update failed, symbol removed');
                    }
                }
                catch(err) {
                    symbols.delete(newSymbol);
                    console.log('Error: ' + err.message + ',');
                    console.log('Form triggered stock update failed, symbol removed');
                }
                
            };
            
            // Add data to send with request
            const data = new FormData();
            let i = 0;
            for (let symbol of symbols) {
                data.append((i++).toString(), symbol);
            }
            data.append('len', i);
            // Send request
            request.send(data);
        }
        // Clear rows
        document.getElementById('symbol').value = '';
        document.getElementById('submit').disabled = true;
        // Don't submit form (don't reload page)
        return false;
    };
});

document.addEventListener('DOMContentLoaded', () => {
    setTimeout(timeoutStocks, 10000);
    function timeoutStocks() {
        
        // Updates all stocks in symbols
        updateStocks();
        // Repeat every 10 seconds
        setTimeout(timeoutStocks, 10000);
        
    }
});


function updateStocks() {
    if (symbols.size !== 0) {
        // Initialize new request
        const request = new XMLHttpRequest();
        request.open('POST', '/stocks/quote', true);
        
        // Callback function for when request completes
        request.onload = () => {
                
            // Extract JSON data from request
            try {
                const data = JSON.parse(request.responseText);
                // Update the result div
                if (data.success) {
                    const tBody = document.getElementById('tBody');
                    tBody.innerHTML = '';
                    for (let i = 0; i < data.stocks.length; i++) {
                        let row = tBody.insertRow(0);
                        for (let c=0; c < 3; c++) {
                            let tempCell = row.insertCell(c);
                            if (tempCell.cellIndex === 1)
                                tempCell.classList.add('priceCell');
                            else if (tempCell.cellIndex === 0)
                                tempCell.classList.add('testing');
                        }
                        row.cells[0].innerHTML = data.stocks[i].name;
                        row.cells[1].innerHTML = data.stocks[i].price;
                        row.cells[2].innerHTML = data.stocks[i].symbol;
                    }
                    for (let cell = 0; cell < document.getElementsByClassName("priceCell").length; cell++) {
                        document.getElementsByClassName('priceCell')[cell].style.backgroundColor = 'rgb(255, 216, 178)';
                    }
                    fade(document.getElementsByClassName('priceCell'), [255, 216, 178], [255, 255, 255], 200, 5);
                    console.log('Timer triggered stock update successful');
                } else {
                    console.log('Timer triggered stock update failed');
                }
            }
            catch(err) {
                console.log('Error: ' + err.message + ',');
                console.log('Timer triggered stock update failed');
            }
                
        };
            
        // Add data to send with request
        const data = new FormData();
        let i = 0;
        for (let symbol of symbols) {
            data.append((i++).toString(), symbol);
        }
        data.append('len', i);
        // Send request
        request.send(data);
    }
}


function fade(elems, from, to, time, steps) {
    var changeR = (to[0] - from[0]) / steps;
    var changeG = (to[1] - from[1]) / steps;
    var changeB = (to[2] - from[2]) / steps;
    
    var current = from;
    var count = 0;
    var elemsLength = elems.length;
    var timer = setInterval(() => {
        current[0] = parseInt(current[0] + changeR);
        current[1] = parseInt(current[1] + changeG);
        current[2] = parseInt(current[2] + changeB);
        for (let cell = 0; cell < elemsLength; cell++) {
            elems[cell].style.backgroundColor = 'rgb(' + current.toString() + ')';
        }
        count++;
        if (count >= steps) {
            for (let cell = 0; cell < elemsLength; cell++) {
                if (cell % 2 === 0) {
                    elems[cell].style.backgroundColor = "rgba(0, 0, 0, .001)";
                } else {
                    elems[cell].style.backgroundColor = 'rgb(' + to.toString() + ')';
                }
            }
            clearInterval(timer);
        }
    }, parseInt(time / steps));
}
