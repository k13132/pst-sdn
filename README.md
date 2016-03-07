Installation of VM used in A0M32PST

- `./controller file.py` - start Ryu controller with _file.py_ (_hub.py_ is used if file is omitted)
- `./mininet.sh` - run mininet with single topology and 5 hosts, enable OpenFlow 1.3, connect to controller at *127.0.0.1:6333* and return mininet console

# Additional topics

You can establish GRE tunnels between multiple Open VSwitches and create L2/L3 overlay networkd. 

```
ovs-vsctl add-port br0 gre0 -- set interface gre0 type=gre options:remote_ip=second_endpoint_ip
```

More information can be found at <http://blog.scottlowe.org/2013/05/07/using-gre-tunnels-with-open-vswitch/>
