# OpenVPN for Docker

**the original project - [jpetazzo/dockvpn](https://github.com/jpetazzo/dockvpn)** and it has its own [automatic build on dockerhub](https://hub.docker.com/r/jpetazzo/dockvpn/). 
 
## Quick instructions:

### With git

Parameters may be setted via environment variables or edited in `Dockerfile`.
Example below with environment variables. All `-e` parameters may be ommited.
```bash
git clone https://github.com/strayge/dockvpn.git
cd dockvpn
docker build -t dockvpn .
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

docker run -ti -d -v $DIR/configs:/etc/openvpn --net=host --privileged --restart unless-stopped \
--name dockvpn -e PORT_TCP=1195 -e PORT_UDP=1195 -e PORT_CONTROL=8000 -e CONTROL_USERNAME=username123 \
-e CONTROL_PASSWORD=password456 -e EXTERNAL_ADDRESS="yourdomain.com" dockvpn
```

### With docked hub

```bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

docker run -ti -d -v $DIR/configs:/etc/openvpn --net=host --privileged --restart unless-stopped \
--name dockvpn -e PORT_TCP=1195 -e PORT_UDP=1195 -e PORT_CONTROL=8000 -e CONTROL_USERNAME=username123 \
-e CONTROL_PASSWORD=password456 -e EXTERNAL_ADDRESS="yourdomain.com" strayge/dockvpn
```

Config files available at web interface.
Address shown at the indicated URL after start. You will get a
certificate warning, since the connection is done over SSL, but we are
using a self-signed certificate.
The file can be used immediately as an OpenVPN profile. It embeds all the
required configuration and credentials. It has been tested successfully on
Linux, Windows, and Android clients. If you can test it on OS X and iPhone,
let me know!

**Note:** there is a [bug in the Android Download Manager](
http://code.google.com/p/android/issues/detail?id=3492) which prevents
downloading files from untrusted SSL servers; and in that case, our
self-signed certificate means that our server is untrusted. If you
try to download with the default browser on your Android device,
it will show the download as "in progress" but it will remain stuck.
You can download it with Firefox; or you can transfer it with another
way: Dropbox, USB, micro-SD card...

If you reboot the server (or stop the container) and you `docker run`
again, all your configuration preserved.

## How does it work?

When the `strayge/dockvpn` image is started, it generates:

- Diffie-Hellman parameters,
- a private key,
- a self-certificate matching the private key,
- two OpenVPN server configurations (for UDP and TCP),
- an OpenVPN client profiles different for each user.

Then, it starts two OpenVPN server processes (by default on 1195/udp and 1195/tcp).

The configuration is located in `/etc/openvpn`, and the Dockerfile
declares that directory as a volume. 
Web interface with basic http authentoication starts on 8000/tcp.
If username and password not specified web server will not be started.

## OpenVPN details

We use `tun` mode, because it works on the widest range of devices.
`tap` mode, for instance, does not work on Android, except if the device
is rooted.

The topology used is `net30`, because it works on the widest range of OS.
`p2p`, for instance, does not work on Windows.

The TCP server uses `192.168.255.0/25` and the UDP server uses
`192.168.255.128/25`.

The client profile specifies `redirect-gateway def1`, meaning that after
establishing the VPN connection, all traffic will go through the VPN.
This might cause problems if you use local DNS recursors which are not
directly reachable, since you will try to reach them through the VPN
and they might not answer to you. If that happens, use public DNS
resolvers like those of Google (8.8.4.4 and 8.8.8.8) or OpenDNS
(208.67.222.222 and 208.67.220.220).
