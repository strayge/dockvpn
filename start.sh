DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
docker run -ti -v $DIR/configs:/etc/openvpn --net=host --privileged --restart unless-stopped --name dockvpn dockvpn
