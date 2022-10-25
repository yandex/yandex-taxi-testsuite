daemonize yes
${protected_mode_no}
port ${port}
tcp-backlog 511
bind ${host}
timeout 0
tcp-keepalive 0
loglevel notice
databases 16
save ""
cluster-enabled yes
cluster-config-file nodes_${port}.conf
cluster-node-timeout 5000
