# Airport Service API

The RESTful API is designed to manage flight-related information and operations. This service provides a convenient way to interact with different resources such as airplane types, airplanes, crews, airports, routes, flights, and orders.

## Run without Docker

Python3 must already be installed!

```shell
git clone https://github.com/vitalii-babiienko/airport-service-api.git
cd airport-service-api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
* Configure your DB.
* Create a .env file by copying the .env.sample file and populate it with the required values.
```shell
python manage.py migrate
python manage.py runserver
```

## Run with Docker

Docker must already be installed!

```shell
git clone https://github.com/vitalii-babiienko/airport-service-api.git
cd airport-service-api
docker-compose up
```

## Get access

* Create a new user via [api/user/register/](http://localhost:8000/api/user/register/).
* Take the access and refresh tokens via [api/user/token/](http://localhost:8000/api/user/token/).
* Refresh the access token via [api/user/token/refresh/](http://localhost:8000/api/user/token/refresh/).

## API Documentation

The API is well-documented with detailed explanations of each endpoint and its functionalities. The documentation provides sample requests and responses to help you understand how to interact with the API. The documentation is available via [api/doc/swagger/](http://localhost:8000/api/doc/swagger/).
