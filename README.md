Catalog Application

The project is written in Python and uses the Flask Library. Functions like Jasonify, routing, GET/POST and render_template are used. Authentication is done via Google account. 

FILES:
All of the files are included in this download.

Root folder holds catalog_Db.py, CatalogItems.py, client_secrets.py
catalogProject.py, ItemCatalog.db

Static folder includes CSS code.

Templates folder holds HTML code for each page of the application.

You will need to edit the client_secrets.py and login.html files.
Please visit https://console.developers.google.com and obtain your personal API key. Once obtained please copy and paste it into both files.

To run the application:
1. Open terminal and navigate to this project files
2. Type in vagrant up and then vagrant ssh. (Vagrant environment is included in the files)
3. Once logged into vagrant. Type in python catalog_Db.py to create the database. (Can skip step 3 and 4 if you wish to use the database file provided with the project)
4. Then run python CatalogItems.py to populate the database
5. Run python catalogProject.py and navigate to localhost:8000 in your browser.