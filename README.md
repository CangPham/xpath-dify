# How to install
## Install container
```
cd ./docker
docker compose build
docker compose -p hota-dify-test-v1 up -d --no-build
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
localhost:5001
```
### API for dashboard
```
localhost:8501
```

## Allow port for access by port on public domain or ip
```
sudo ufw allow 5001
```
