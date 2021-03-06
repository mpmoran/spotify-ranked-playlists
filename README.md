# README

## how to query log

```sh
csvsql -d '|' -q '`' --query "select message from log where module_name = 'root';" log.csv | csvlook
```
