# FinLife

FinLife: Yet another financial manager
A project to learn new technologies and to have a financial manager
with features that I have not found in other apps.

## This project is developed using:
* Ubuntu 16.04 as OS
* Python 3 as programming language
* virtualenv and virtualenvwrapper to manage virtual environments

## Instructions
If you want to use virtualenvwrapper, open you terminal and:

    $ sudo pip install virtualenvwrapper

Open your .bashrc file and add these lines at the end:

    export WORKON_HOME=$HOME/.virtualenvs
    source /usr/local/bin/virtualenvwrapper.sh


Restart your terminal, go to project directory, create your virtualenv and install requirements:

    $ mkvirtualenv financial-life-backend
    $ workon financial-life-backend
    $ pip install -r requirements.txt

### Database
If you don't have PostgreSQL, install it:

    $ sudo apt install postgresql

Then, create the database:

    $ sudo su postgres
    $ psql
    $ CREATE ROLE finlife SUPERUSER LOGIN PASSWORD 'finlife';
    $ CREATE DATABASE finlife;
    $ ALTER DATABASE finlife OWNER TO finlife;

Start Alembic to create migrations for the new database:

    $ python manage.py db init

When a model is created or changed, create migrations:

    $ python manage.py db migrate

Then, uptade the database:

    $ python manage.py db upgrade

Now you can run the api with:

    $ python run.py

That's it! Now the api is running and you can send requests to it. Use curl or Postman to test the API.

## Examples
### Creating user

    curl -X POST \
      http://local-finlife.com/api/users \
      -H 'cache-control: no-cache' \
      -H 'content-type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW' \
      -F name=User \
      -F email=user@mail.com \
      -F password=user


### Creating account:
Soon...


## References
[Flask mega tutorial](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world)
[InCeres base-api](https://github.com/InCeres/base-api)