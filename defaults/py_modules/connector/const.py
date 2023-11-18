# Hardcoded protocol version
KDE_CONNECT_PROTOCOL_VERSION = 7

# KDE Connect UDP Discovery port
KDE_CONNECT_DISCOVERY_PORT = 1716

# TCP port hardcoded only in this implementation
# In general, client should extract suitable tcp port from
# IDENTITY packet
KDE_CONNECT_TCP_PORT = KDE_CONNECT_DISCOVERY_PORT + 1

HTTP_INTERNAL_PORT = KDE_CONNECT_TCP_PORT + 1

LOCAL_CERTIFICATE_FILE = "local.crt"
LOCAL_PRIVATE_KEY_FILE = "local.key"
LOCAL_PUBLIC_KEY_FILE = "local.pub"
