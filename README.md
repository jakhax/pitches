Pitches
===================

- - - -
Author: [Jack Ogina](https://github.com/jakhax)
## Description
[Pitches](https://github.com/jakhax/pitches.git) is a web application that allows users to use that one minute wisely. The users will submit their one minute pitches and other users will vote on them and leave comments to give their feedback on them.
The pitches are organized by category. You can have different categories like pickup lines, interview pitch , product pitch, promotion pitch.

------------------------------------------------------------------------

## User Requirements

1. user should see the pitches other people have posted.
2. user should vote on the pitch they liked and give it a downvote or upvote.
3. user should comment on the different pitches and leave feedback.
4. user should submit a pitch in any category.
5. user should view the different categories.

## Features

+ [x] Create and display pitches based on categories
+ [x] Create category for pitches
+ [x] Display trending pitches based on day, week, month, year.
+ [x] Display the latest pitches and comments.
+ [x] Create user accounts with roles 
+ [x] Send email verification to users with secret token that expires after sometime
+ [x] Send email to admin user when a new user signs up.
+ [x] Generate [gravatars](https://en.gravatar.com/site/implement/images/python/)
+ [x] Editing user profiles
+ [x] Admin and moderator user with admin roles : create/delete/edit pitches topics, other users pitches and user's roles.
+ [x] User's messaging capability
+ [ ] Show user's with the most pitches upvotes
+ [ ] Multiple language support using [flask-babel](https://pythonhosted.org/Flask-Babel/)

## Specifications
[Specifications file](https://github.com/jakhax/pitches/blob/master/specs.md)

## Quickstart
```
usage: manage.py [-?]
                 {shell,insert_fake_data,db,insert_initial_data,server,dbshell,test,runserver}
                 ...

positional arguments:
  {shell,insert_fake_data,db,insert_initial_data,server,dbshell,test,runserver}
    shell               Runs a Python shell inside Flask application context.
    insert_fake_data    Adds fake data to database.
    db                  Perform database migrations
    insert_initial_data
                        Adds initial data to database.
    server              Runs the Flask development server i.e. app.run()
    dbshell             Run DB shell.
    test                Run the unit tests.
    runserver           Runs the Flask development server i.e. app.run()

optional arguments:
  -?, --help            show this help message and exit
  ```

## Setup

### Requirements
This project was created on a debian linux platform but should work on other unix based[not limited to] sytems.
* Tested on Debian Linux
* Python 2.7

### Cloning the repository
```bash
git clone https://github.com/jakhax/pitches.git && cd pitches
```

### Creating a virtual environment

```bash
python2.7 -m virtualenv virtual-pitches
source virtual-pitches/bin/activate
```
### Installing dependencies
```bash
pip3 install -r requirements
```

### Prepare environmet variables
```bash
 export MAIL_USERNAME=YOUR EMAIL
 export MAIL_PASSWORD=EMAIL PASSWORD
 export ADMIN_MAIL_USERNAME=ADMIN ACCOUNT EMAIL
 export DB_USER=forum_app
 export DATABASE_URL=POSTGRESQL DATABASE PATH WITH DRIVER
```

### Database migrations

```bash
# first initialize the database if the migrations folder does not exist
python manage.py db init
# create  a migration
python manage.py db migrate -m "initial migration"
# upgrade
python manage.py db upgrade
# insert initial data
python manage.py insert_initial_data
```

#### fake data for development 

using [Forgery_py](http://tomekwojcik.github.io/ForgeryPy/) library you can generate fake data and insert it to the database for testing 
the web app during development check out the example below for creating fake users
```python
def generate_fake_users(count=100):
    seed()
    for i in range(count):
        user_name = forgery_py.internet.user_name(True)[:32]
        u = User(email=forgery_py.internet.email_address(),
                 username=user_name,
                 username_normalized=user_name.lower(),
                 password=forgery_py.lorem_ipsum.word(),
                 confirmed=True,
                 name=forgery_py.name.full_name()[:64],
                 homeland=forgery_py.address.city()[:64],
                 about=forgery_py.lorem_ipsum.sentence(),
                 created_at=forgery_py.date.date(True))
        db.session.add(u)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
```
### Running Tests
```bash
python manage.py test
```

### Running the server 
#### Development mode
The following are enabled in development mode 
```python 
class DevConfig(Config):
    DEBUG = True
    TESTING = True

```

Run server
```bash 
# starting server by defaut will run it in development mode
python manage.py server
```
#### production mode
```python
class ProdConfig(Config):
    DEBUG = False
    TESTING = False
    DEBUG_TB_INTERCEPT_REDIRECTS = False
```

make the following change to the config.py script
'''python
config=ProdConfig()
'''

Run server
```bash
python manage.py runserver -h 0.0.0.0 -p 8000
```
### Deploying to heroku
Set the configuration to production mode
```bash
heroku create appname
heroku heroku addons:create heroku-postgresql
git push heroku master
heroku run python2.7 manage.py db upgrade
```

## Live Demo

The web app can be accessed from the following link
[https://pitch3es.herokuapp.com/](https://pitch3es.herokuapp.com/)


## Technology used

* [Python3.6](https://www.python.org/)
* [Flask](http://flask.pocoo.org/)
* [Heroku](https://heroku.com)
* [Celery](http://www.celeryproject.org/)
* [Gravatar](https://en.gravatar.com)

## Contributing

- Git clone [https://github.com/jakhax/pitches.git](https://github.com/jakhax/pitches.git) 
- Make the changes.
- Write your tests on `tests/`
- If everything is OK. push your changes and make a pull request.

## License ([MIT License](http://choosealicense.com/licenses/mit/))

This project is licensed under the MIT Open Source license, (c) [Jack ogina](https://github.com/jakhax)