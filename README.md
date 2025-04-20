# How to install
## Image and container
### Intall
```
cd ./docker
docker compose build
docker compose -p hota-dify-test-v1 up -d --no-build
```
### Verify
check if hota-dify-test-v1 exists
```
docker ps
```
### Run
```
docker start hota-dify-test-v1
```

## List port of project
### Dify web ui
```
0.0.0.0:80
0.0.0.0:443 (ssl)
localhost:80
localhost:443 (ssl)
```
### Dashboard
```
localhost:8501
```
### API for dashboard
```
localhost:5001
```

## Allow port for access by port on public domain or ip
```
sudo ufw allow 8501
```
