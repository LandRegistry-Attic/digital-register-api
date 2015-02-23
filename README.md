# digital-register-api

This is the repo for the backend of the digital register service. It is written in Python, with the Flask framework.  

### Digital Register API build status

[![Build Status](http://54.72.23.130/job/digital-register-api-unit-test%20(Master)/badge/icon)](http://54.72.23.130/job/digital-register-api-unit-tests%20(Master)/)

### Digital Register Acceptance tests status

[![Build Status](http://54.72.23.130/job/digital-register-frontend-acceptance-tests/badge/icon)](http://54.72.23.130/job/digital-register-frontend-acceptance-tests/)

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

## Jenkins builds 

We use three separate builds:
- [branch](http://54.72.23.130/job/digital-register-api-unit-test%20(Branch)/)
- [master](http://54.72.23.130/job/digital-register-api-unit-test%20(Master)/)
- [acceptance](http://54.72.23.130/job/digital-register-frontend-acceptance-tests/)
