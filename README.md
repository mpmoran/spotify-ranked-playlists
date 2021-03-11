# README

## Create dev Docker container and run it

```sh
$ docker build -t flask-container . && docker run --rm -p 5000:5000 flask-container
```

## Create Lightsail resource

```sh
$ aws lightsail create-container-service \
    --service-name ranked-spotify-playlists \
    --power micro \
    --scale 1
```

# Push app to Lightsail container

```sh
$ aws lightsail push-container-image \
    --service-name ranked-spotify-playlists \
    --label flask-container \
    --image flask-container

$ aws lightsail create-container-service-deployment \
    --service-name ranked-spotify-playlists \
    --containers file://containers.json \
    --public-endpoint file://public-endpoint.json
```

## Get container endpoint

```sh
$ aws lightsail get-container-services --service-name ranked-spotify-playlists
```

## how to query log

```sh
$ csvsql -d '|' -q '`' --query "select message from log where module_name = 'root';" log.csv | csvlook
```

## Sources

1. https://aws.amazon.com/getting-started/hands-on/serve-a-flask-app/?trk=gs_card