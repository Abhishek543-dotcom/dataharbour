docker pull postgres:14.15-alpine3.21
mkdir -p ~/postgresql/data
docker run -d \
  --name postgres \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=strongpassword \
  -e POSTGRES_DB=mydatabase \
  -p 5432:5432 \
  -v ~/postgresql/data:/var/lib/postgresql/data \
  postgres
