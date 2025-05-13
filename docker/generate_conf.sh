#!/bin/bash

# Export these variables then run it

if [ -z "$DOMAIN_NAME" ]; then
    echo "Error: DOMAIN_NAME environment variable is not set."
    exit 1
fi

if [ -z "$HOST_IP" ]; then
    echo "Error: HOST_IP environment variable is not set."
    exit 1
fi

if [ -z "$TURN_SECRET" ]; then
    echo "Error: TURN_SECRET environment variable is not set."
    exit 1
fi

COTURN_CONF="coturn/turnserver.conf"

cp coturn/turnserver.conf.template $COTURN_CONF

sed -i "s|\${DOMAIN_NAME}|$DOMAIN_NAME|g" "$COTURN_CONF"
sed -i "s|\${HOST_IP}|$HOST_IP|g" "$COTURN_CONF"
sed -i "s|\${TURN_SECRET}|$TURN_SECRET|g" "$COTURN_CONF"

cp nginx/nginx.conf.template nginx/nginx.conf

sed -i "s|\${DOMAIN_NAME}|$DOMAIN_NAME|g" nginx/nginx.conf

chmod 644 "$COTURN_CONF"
chmod 644 nginx/nginx.conf
