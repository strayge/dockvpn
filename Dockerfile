FROM ubuntu:xenial

RUN apt-get update -q && \
    apt-get install -qy openvpn iptables socat curl wget python2.7 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# get easyrsa 3.0 (2.2 in repos)
RUN mkdir -p /etc/easyrsa
RUN cd /tmp && \
    wget https://github.com/OpenVPN/easy-rsa/releases/download/v3.0.4/EasyRSA-3.0.4.tgz && \
    tar xf EasyRSA-3.0.4.tgz && \
    cd EasyRSA-3.0.4 && \
    cp -r easyrsa openssl-easyrsa.cnf x509-types /etc/easyrsa && \
    cd /tmp && \
    rm -r EasyRSA-3.0.4 EasyRSA-3.0.4.tgz

ADD ./bin /usr/local/sbin
VOLUME /etc/openvpn

ENV PORT_TCP 1195
ENV PORT_UDP 1195
ENV PORT_CONTROL 8000
ENV SSL 1
#ENV CONTROL_USERNAME username123
#ENV CONTROL_PASSWORD password456

# domain name can be specified here for generating ovpn configs
ENV EXTERNAL_ADDRESS ""

EXPOSE ${PORT_TCP}/tcp ${PORT_UDP}/udp ${PORT_CONTROL}/tcp
CMD run
