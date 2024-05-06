docker image rm z46_projekt_gateway
docker build -t z46_projekt_gateway -f gateway/Dockerfile .

docker image rm z46_projekt_sensor
docker build -t z46_projekt_sensor -f sensor/Dockerfile .

docker image rm z46_projekt_user
docker build -t z46_projekt_user -f user/Dockerfile .


