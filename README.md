# DEPRECATED

Please see this newer project: [FDDB-Exporter](https://github.com/itobey/fddb-exporter)

# Fddb-Calories-Exporter

Exports calories from fddb.info (aggregated to a daily level) to a postgres database. This is a small project I used to learn Python and dataframes.

## Prerequisites

- a running postgres database with a table set up (see below)
- an account on fddb.info for which you want to export the data
- the fddb cookie necessary (see below)
- Docker or Python to run the exporter

## How it works

The python script connects to fddb.info and downloads the `tagebuch` containing all information entered in [FDDB-Extender](https://play.google.com/store/apps/details?id=com.fddb&hl=de&gl=US) (or some other platform). To authenticate it needs the user and password for the site, as well as a specific cookie. This cookie is valid until you are logged out and without it beeing passed as a cookie header, the requests will just return a message, that there's no data available. You can retrieve it for example by using Chrome dev tools on the network tab, when you open fddb.info after beeing logged in. Remember that if you log out of your current browser session, the cookie will get invalid and the script will fail. I may redesign the script to obtain the cookie on login in the future.

Example:

![Chrome Dev Tools](docs/chrome-dev-tools.png)

After downloading the csv-file it will transform it into a python dataframe, do some calculations to aggregate the calories per day and insert it into the fddb table in postgres. If an entry already exists for that day, it will update it. Empty values (days with no calories recorded) will be ignored.

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

You may just run my [prebuilt image](https://hub.docker.com/r/itobey/fddb-calories-exporter) or build it yourself. When using alpine as a base image, keep in mind that the requirements (like pandas) have to be compiled from source and it may take a long time. Also I do not recommend using a development version of the regular debian python image, as I ran into problems with requirements when installing dependencies with `pip`.

I also recommend using an `.env` file to store all variables and pass it to the container on runtime. Just add the variables mentioned above in a file delimited by a `=`.

`docker run --rm --network=<the-network-with-postgres> --env-file /path/to/.env fddb-calories-exporter python exporter.py`

This can be run in a cronjob (or k8s job, if you have that) to update the database every day.

## Kubernetes

When I have migrated to K3s I decided to run this as a Kubernetes Cronjob. I'm using helm sops with ArgoCD to encrypt the environment variables. Feel free to use other tools for this job.

```
apiVersion: batch/v1
kind: CronJob
metadata:
  name: fddb-exporter
spec:
  schedule: "55 23 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: fddb-exporter
            image: itobey/fddb-calories-exporter
            imagePullPolicy: IfNotPresent
            env:
            - name: FDDB_USER
              value: "{{ .Values.fddb.user}}" 
            - name: FDDB_PW
              value: "{{ .Values.fddb.pw}}" 
            - name: FDDB_COOKIE
              value: "{{ .Values.fddb.cookie}}" 
            - name: FDDB_POSTGRES
              value: "{{ .Values.fddb.postgres}}" 
            command:
            - python
            - exporter.py
          restartPolicy: OnFailure
```

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
