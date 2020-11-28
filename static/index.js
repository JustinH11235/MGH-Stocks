document.addEventListener('DOMContentLoaded', () => {
    setTimeout(updateStocks, 750);
    function updateStocks() {
        
        // Initialize new request
        const request = new XMLHttpRequest();
        request.open('GET', 'https://mgh-stocks.herokuapp.com?xhr=true', true);

        // Callback function for when request completes
        request.onload = () => {
            
            // Extract JSON data from request
            var data = JSON.parse(request.responseText);

            // Update the result div
            if (data.success) {
                var tBody = document.getElementById('portfolio').tBodies[0];
                tBody.innerHTML = "<tr><td>CASH</td><td colspan='3'></td><td id='cash'></td></tr>";
                for (let i = 0; i < data.stocks.length; i++) {
                    let row = tBody.insertRow(tBody.rows.length - 1);
                    for (let c=0; c < 5; c++) {
                        row.insertCell(c);
                    }
                    row.cells[0].innerHTML = data.stocks[i].symbol;
                    row.cells[1].innerHTML = data.stocks[i].name;
                    row.cells[2].innerHTML = data.stocks[i].shares;
                    row.cells[3].innerHTML = data.stocks[i].price;
                    row.cells[4].innerHTML = data.stocks[i].subtotal;
                }
                document.getElementById('cash').innerHTML = data.cash;
                document.getElementById('total').innerHTML = data.total;
                for (let high = 0; high < document.getElementsByClassName("highlight").length; high++) {
                    document.getElementsByClassName('highlight')[high].style.backgroundColor = 'rgb(255, 242, 229)';
                }
                fade(document.getElementsByClassName('highlight'), [255, 242, 229], [255, 255, 255], 200, 5);
                console.log('Timer triggered stock update successful');
            } else {
                console.log('Timer triggered stock update failed');
            }
            
        };

        // Send request
        request.send();
        
        // Repeat in 10 seconds
        setTimeout(updateStocks, 10000);
        
    }
});


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
            let counter = 0;
            for (let cell = 0; cell < elemsLength; cell++) {
                // if (counter++ % 2 === 0) {
                    // elems[cell].style.backgroundColor = "rgba(0, 0, 0, .001)";
                // } else {
                    elems[cell].style.backgroundColor = 'rgb(' + to.toString() + ')';
                // }
            }
            clearInterval(timer);
        }
    }, parseInt(time / steps));
}
