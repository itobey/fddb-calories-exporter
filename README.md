# Fddb-Calories-Exporter

Exports calories from fddb.info (aggregated to a daily level) to a postgres database. This is a small project I used to learn Python and dataframes.

## Prerequisites

- a running postgres database with a table set up (see below)
- an account on fddb.info for which you want to export the data
- the fddb cookie necessary (see below)
- Docker or Python to run the exporter

## How it works

The python script connects to fddb.info and downloads the `tagebuch` containing all information entered in [FDDB-Extender](https://play.google.com/store/apps/details?id=com.fddb&hl=de&gl=US) (or some other platform). To authenticate it needs the user and password for the site, as well as a specific cookie. This cookie represents most likely the internal user id of fddb.info and without it beeing passed as a cookie header, the requests will just return a message, that there's no data available. You can retrieve it for example by using Chrome dev tools on the network tab, when you open fddb.info after beeing logged in.

Example:

![Chrome Dev Tools](docs/chrome-dev-tools.png)

After downloading the csv-file it will transform it into a python dataframe, do some calculations to aggregate the calories per day and insert it into the fddb table in postgres. If an entry already exists for that day, it will ignore it (so run it after having entered all data for the day, if you want to track it daily). Empty values (days with no calories recorded) will be ignored as well.

## Database

In it's current state the script expects a table called `fddb` with a `date` and `kj` column. Feel free to change it or just use this to set up the database:

`CREATE TABLE fddb (date DATE PRIMARY KEY, kj INT);`

If you don't have any postgres running, I recommend simply running postgres by using a docker-compose entry.

```
version: '3'
services:
  postgres:
    image: postgres:12.6
    ports:
      - 5432:5432
    container_name: postgres
    restart: always
    environment:
      POSTGRES_PASSWORD: example
```

## Configuration

The script needs certain variables to function, which are read as environment variables.

| key           | value                                                |
|---------------|------------------------------------------------------|
| FDDB_USER     | user@mail.tld                                        |
| FDDB_PW       | supersecretpassword                                  |
| FDDB_COOKIE   | thecookiementionedabove                              |
| FDDB_POSTGRES | postgresql://postgres:example@postgres:5432/postgres |

FDDB_POSTGRES contains the entire connection string for the postgres database. If you're running the docker image, see below for an approach to set the variables.

## Docker

You may just run my prebuilt image or build it yourself. When using alpine as a base image, keep in mind that the requirements (like pandas) have to be compiled from source and it may take a long time. Also I do not recommend using a development version of the regular debian python image, as I ran into problems with requirements when installing dependencies with `pip`.

I also recommend using an `.env` file to store all variables and pass it to the container on runtime. Just add the variables mentioned above in a file delimited by a `=`.

`docker run --rm --network=<the-network-with-postgres> --env-file /path/to/.env fddb-calories-exporter python exporter.py`

This can be run in a cronjob (or k8s job, if you have that) to update the database every day.

## Benefits

Well, you got the data, obviously. I like to display it in Grafana with some stats as well.

![Chrome Dev Tools](docs/grafana-panel.png)

Just use a simple query to retrieve the information in Grafana.

```
SELECT
  date AS "time",
  kj AS "kcal"
FROM fddb
WHERE
  $__timeFilter(date)
ORDER BY 1
```
