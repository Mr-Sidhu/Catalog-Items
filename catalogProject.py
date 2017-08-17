from flask import Flask, render_template, url_for, redirect, request, jsonify
from flask import flash, g
from flask import session as login_session
import random
import string
from functools import wraps
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from catalog_Db import Base, User, Catalog, CatalogItems

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)
app.secret_key = 'super_secret_key'

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Items Catalog"


engine = create_engine('sqlite:///ItemCatalog.db')
Base.metadata.bind = engine

DBsession = sessionmaker(bind=engine)
session = DBsession()


@app.route('/login/')
def showLogin():
    """Login page for google signIn"""
    state = ''.join(random.choice(string.ascii_uppercase +
                    string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            return redirect(url_for('showLogin'))
        return f(*args, **kwargs)
    return decorated_function


def newUser(login_session):
    createUser = User(name=login_session['username'],
                      email=login_session['email'])
    session.add(createUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def userInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def userID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """This method is used for login. GET method is not allowed."""
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already\
                                 connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # code to see if user already exists.
    user_id = userID(login_session['email'])
    if not user_id:
        user_id = newUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;\
                  border-radius: 150px;-webkit-border-radius: 150px;\
                  -moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


@app.route('/gdisconnect')
def gdisconnect():
    """Disconnect method. Accessed by the logout button."""
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
                                 json.dumps('Current user not connected.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' %\
          login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token\
                                 for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/')
@app.route('/catalog/')
def catalog():
    """Prints out the catalog and ten most recent items added"""
    catalog = session.query(Catalog).all()
    items = session.query(
                          CatalogItems).order_by(
                          CatalogItems.id.desc()).limit(8)
    if 'username' not in login_session:
        return render_template('publicCatalog.html',
                               catalog=catalog, items=items)
    else:
        return render_template('catalog.html', catalog=catalog, items=items)


@app.route('/catalog/<int:catalog_id>/')
def catalogItems(catalog_id):
    """Prints out items of a selected catalog"""
    catalog = session.query(Catalog).all()
    catalog_selected = session.query(Catalog).filter_by(id=catalog_id).one()
    items = session.query(CatalogItems).filter_by(catalog_id=catalog_id)
    if 'username' not in login_session:
        return render_template('publicCatalogItem.html',
                               catalog_selected=catalog_selected,
                               catalog=catalog, items=items)
    else:
        return render_template('catalogItem.html',
                               catalog_selected=catalog_selected,
                               catalog=catalog, items=items)


@app.route('/catalog/<int:catalog_id>/<int:catalogItem_id>/edit/',
           methods=['GET', 'POST'])
@login_required
def catalogItemsEdit(catalog_id, catalogItem_id):
    """Edits a selected catalog item"""
    editedItem = session.query(CatalogItems).filter_by(id=catalogItem_id).one()
    if login_session['email'] == editedItem.userEmail:
        if request.method == 'POST':
            if request.form['name']:
                editedItem.name = request.form['name']
            if request.form['description']:
                editedItem.description = request.form['description']
            if request.form['catalog']:
                editedItem.catalog_id = request.form['catalog']

            session.add(editedItem)
            session.commit()
            return redirect(url_for('catalog'))
        else:
            return render_template('editCatalogItem.html',
                                   catalog_id=catalog_id,
                                   catalogItem_id=catalogItem_id,
                                   editedItem=editedItem)
    else:
        return "You do not have permission to edit this item."


@app.route('/catalog/new/', methods=['GET', 'POST'])
@login_required
def newCatalogItem():
    """Add new item to catalog"""
    if request.method == 'POST':
        newItem = CatalogItems(
                               name=request.form['name'],
                               description=request.form['description'],
                               userEmail=login_session['email'],
                               catalog_id=request.form['catalog'])
        session.add(newItem)
        session.commit()
        return redirect(url_for('catalog'))
    else:
        return render_template('newCatalogItem.html')


@app.route('/catalog/<int:catalog_id>/<int:catalogItem_id>/delete/',
           methods=['GET', 'POST'])
@login_required
def catalogItemsDelete(catalog_id, catalogItem_id):
    """Deletes a selected catalog item"""
    deletedItem = session.query(
                                CatalogItems).filter_by(
                                id=catalogItem_id).one()
    if login_session['email'] == deletedItem.userEmail:
        if request.method == 'POST':
            session.delete(deletedItem)
            session.commit()
            return redirect(url_for('catalog'))
        else:
            return render_template('deleteCatalogItem.html',
                                   catalog_id=catalog_id,
                                   catalogItem_id=catalogItem_id,
                                   deletedItem=deletedItem)
    else:
        return "you do not have permission to delete this item."


@app.route('/catalog/<int:catalog_id>/<int:catalogItem_id>/info/',
           methods=['GET'])
def itemInfo(catalog_id, catalogItem_id):
    """Description page for catalog items. Edit and
       Delete links appear depending on login"""
    selected = session.query(CatalogItems).filter_by(id=catalogItem_id).one()
    if 'username' not in login_session:
        return render_template('publicItemInfo.html', catalog_id=catalog_id,
                               catalogItem_id=catalogItem_id,
                               selected=selected)
    else:
        return render_template('itemInfo.html', catalog_id=catalog_id,
                               catalogItem_id=catalogItem_id,
                               selected=selected)


@app.route('/catalog/JSON/')
def catalogJSON():
    """creates a JSON of catalog data"""
    catalog = session.query(Catalog).all()
    return jsonify(catalog=[c.serialize for c in catalog])


@app.route('/items/JSON/')
def catalogItemJSON():
    """Creates a JSON endpoint of catalogItems data"""
    items = session.query(CatalogItems).all()
    return jsonify(items=[i.serialize for i in items])


@app.route('/item/<int:catalogItem_id>/JSON/')
def catalogOneItemJSON(catalogItem_id):
    """Creates a JSON endpoint of single catalog Item"""
    items = session.query(CatalogItems).filter_by(id=catalogItem_id).one()
    return jsonify(items=[items.serialize])


if __name__ == "__main__":
    """The first method that runs"""
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
