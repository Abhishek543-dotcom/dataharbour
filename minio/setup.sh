docker pull minio/minio
mkdir -p ~/minio/data
docker run -d \
  --name minio \
  -p 9000:9000 \
  -p 9090:9090 \
  -v ~/minio/data:/data \
  -e MINIO_ROOT_USER=admin \
  -e MINIO_ROOT_PASSWORD=strongpassword \
  minio/minio server /data --console-address ":9090"
# to open in browser use http://localhost:9090