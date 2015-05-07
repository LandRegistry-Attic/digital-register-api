# digital-register-api

This is the repo for the backend of the digital register service. It is written in Python, with the Flask framework.  

### Digital Register API build status

[![Build Status](http://52.16.47.1/job/digital-register-api-unit-test%20(Master)/badge/icon)](http://52.16.47.1/job/digital-register-api-unit-test%20(Master)/)

### Digital Register Acceptance tests status

[![Build Status](http://52.16.47.1/job/digital-register-frontend-acceptance-tests/badge/icon)](http://52.16.47.1/job/digital-register-frontend-acceptance-tests/)

## Setup

To create a virtual env, run the following from a shell:

```  
    mkvirtualenv -p /usr/bin/python3 digital-register-api
    source environment.sh
    pip install -r requirements.txt
```

## Run the tests

To run the tests for the Digital Register, go to its folder and run `lr-run-tests`. 

## Run the acceptance tests

To run the acceptance tests for the Digital Register, go to the `acceptance-tests` folder inside the `digital-register-frontend` repository and run:
```
   ./run-tests.sh
```

You will need to have a Postgres database running (see `db/lr-start-db` and `db/insert-fake-data` scripts in the [centos-dev-env](https://github.com/LandRegistry/centos-dev-env) project), as well as the digital-register-frontend and digital-register-api applications running on your development VM.
 
## Run the server

### Run in dev mode

To run the server in dev mode, execute the following command:

    ./run_flask_dev.sh

### Run using gunicorn

To run the server using gunicorn, activate your virtual environment
and execute the following commands:

    pip install gunicorn
    gunicorn -p /tmp/gunicorn.pid service.server:app -c gunicorn_settings.py 

## Jenkins builds 

We use three separate builds:
- [branch](http://52.16.47.1/job/digital-register-api-unit-test%20(Branch)/)
- [master](http://52.16.47.1/job/digital-register-api-unit-test%20(Master)/)
- [acceptance](http://52.16.47.1/job/digital-register-frontend-acceptance-tests/)

## Database migrations

We use Flask-Migrate (a project which integrates Flask with Alembic, a migration
tool from the author of SQLAlchemy) to handle database migrations. Every time a
model is added or modified, a migration script should be created and committed
to our version control system.

From inside a virtual environment, and after sourcing environment.sh, run the
following to add a new migration script:

    python3 manage.py db migrate -m "add foobar field"

Should you ever need to write a migration script from scratch (to migrate data
for instance) you should use the revision command instead of migrate:

    python3 manage.py db revision -m "do something complicated"

Read Alembic's documentation to learn more.

Once you have a migration script, the next step is to apply it to the database.
To do this run the upgrade command:

    python3 manage.py db upgrade
