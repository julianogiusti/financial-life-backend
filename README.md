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
```sudo pip install virtualenvwrapper```

Open your .bashrc file and add these lines at the end:  
```
export WORKON_HOME=$HOME/.virtualenvs
source /usr/local/bin/virtualenvwrapper.sh
```

Restart your terminal, go to project directory, create your virtualenv and install requirements:  
```
mkvirtualenv financial-life-backend
workon financial-life-backend
pip install -r requirements.txt
```

Activate the database:  
```flask db upgrade```

Now you can run the api with:  
```flask run```

That's it! Now the api is running and you can send requests to it. Use curl or Postman to test the API.

## Examples
### Creating user
```
curl -X POST \
  http://localhost:5000/api/users \
  -H 'Content-Type: application/json' \
  -H 'cache-control: no-cache' \
  -d '{
  "username": "user",
  "email": "user@email.com",
  "password": "userpassword"
}'
```

### Creating account:
```
curl -X POST \
  http://localhost:5000/api/users/1/accounts \
  -H 'Content-Type: application/json' \
  -H 'cache-control: no-cache' \
  -d '{
  "name": "Bank XYZ",
  "account_type": 2,
  "balance": 2000.75
}'
```
