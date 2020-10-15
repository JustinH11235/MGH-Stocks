# MGH-Stocks
<h1>Directory if you're in need of direction:</h1>

app.py - Main Flask app (backend)

/templates/ - HTML templates that are served to users by app.py, includes jinja code (the {{ }} stuff) which is part of Flask and allows for "real" coding in HTML files (e.g. loops, conditionals, inheritance (extends)). Each file is essentially one page of the web app (index.html is almost always home).

/static/ - Unchanging files. Encompasses JavaScript files that are linked in the HTML of index.html and quote.html pages, my css file (only css that isn't already provided by Bootstrap), etc.
