
## IP Allocation
- 10.254.0.0/16 - Link Nets (Physical P2P): 
    - 10.254.1.0/24 - Spine 1 Downlinks to Leaves
    - 10.254.2.0/24 - Spine 2 Downlinks to leaves
    - Deterministic IP scheme to help when tshooting and be able to see this P2Ps on a traceroute.
- 10.255.0.0./24 - Router IDs (Lo0)
    - Loopback 0 Interface
        - Lo0 functions as the Router ID
        - Lo0 is used ade BGP Source interface for eBGP Peering
        - Router IDs will be configured to match the IP on the Lo0 interface
    - First 8 IPs Allocated to Spines
    - All other IPs Allocated to Leaves
- 10.255.1.0/24 - VTEP (VXLAN Tunnel Endpoint) (Lo1)
    - Loopback 1 Interface
        - Used as the source IP for VXLAN Packets
- MGMT:
    - IPv4: 172.100.100.0/24
        - Leaves: 172.100.100.0/26 (64 IPs)
        - Spines: 172.100.100.64/28 (16 IPs)
        - Spare1: 172.100.100.80/28 (16 IPs)
        - Spare2: 172.100.100.96/27 (32 IPs)
        - Servers: 172.100.100.128/25 (128 IPs)
    - IPv6: 2001:172:100:100::/64
        


### Spine 1 to Leaves - P2Ps 10.254.1.0/24

| Device A Name | Device A Port | Device A IP | Device B Name | Device B Port | Device B IP | P2P Network IP |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| s1 | e1 | 10.254.1.0/31 | l1 | e1 | 10.254.1.1/31 | 10.254.1.0/31 |
| s1 | e2 | 10.254.1.2/31 | l2 | e1 | 10.254.1.3/31 | 10.254.1.2/31 |
| s1 | e3 | 10.254.1.4/31 | l3 | e1 | 10.254.1.5/31 | 10.254.1.4/31 |
| s1 | e4 | 10.254.1.6/31 | l4 | e1 | 10.254.1.7/31 | 10.254.1.6/31 |
| s1 | e5 | 10.254.1.8/31 | l5 | e1 | 10.254.1.9/31 | 10.254.1.8/31 |

### Spine 2 to Leaves - P2Ps 10.254.2.0/24

| Device A Name | Device A Port | Device A IP | Device B Name | Device B Port | Device B IP | P2P Network IP |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| s2 | e1 | 10.254.2.0/31 | l1 | e2 | 10.254.2.1/31 | 10.254.2.0/31 |
| s2 | e2 | 10.254.2.2/31 | l2 | e2 | 10.254.2.3/31 | 10.254.2.2/31 |
| s2 | e3 | 10.254.2.4/31 | l3 | e2 | 10.254.2.5/31 | 10.254.2.4/31 |
| s2 | e4 | 10.254.2.6/31 | l4 | e2 | 10.254.2.7/31 | 10.254.2.6/31 |
| s2 | e5 | 10.254.2.8/31 | l5 | e2 | 10.254.2.9/31 | 10.254.2.8/31 |

### ASNs / Router IDs/ Loopback 0 - 10.255.0.0/24

| Device Name | ASN | Loopback 0 IP (Router ID) |
| :--- | :--- | :--- |
| s1 | 64600 | 10.255.0.1/32 |
| s2 | 64600 | 10.255.0.2/32 |
| l1 | 65001 | 10.255.0.11/32 |
| l2 | 65002 | 10.255.0.12/32 |
| l3 | 65003 | 10.255.0.13/32 |
| l4 | 65004 | 10.255.0.14/32 |
| l5 | 65005 | 10.255.0.15/32 |

### VTEP (VXLAN Soruce) - Loopback 1 - 10.255.1.0/24
| Device Name | Loopback 1 IP (VTEP) |
| :--- | :--- |
| l1 | 10.255.1.11/32 |
| l2 | 10.255.1.12/32 |
| l3 | 10.255.1.13/32 |
| l4 | 10.255.1.14/32 |
| l5 | 10.255.1.15/32 |

### Management Network - Static IPs (Containerlab)

Management network configured in Containerlab topology for out-of-band access.

**Network:** 172.100.100.0/24 (IPv4) and 2001:172:100:100::/64 (IPv6)

#### Spines
| Device Name | Management IPv4 | Management IPv6 |
| :--- | :--- | :--- |
| s1 | 172.100.100.121/24 | 2001:172:100:100::121/64 |
| s2 | 172.100.100.122/24 | 2001:172:100:100::122/64 |

#### Leaves
| Device Name | Management IPv4 | Management IPv6 |
| :--- | :--- | :--- |
| l1 | 172.100.100.61/24 | 2001:172:100:100::61/64 |
| l2 | 172.100.100.62/24 | 2001:172:100:100::62/64 |
| l3 | 172.100.100.63/24 | 2001:172:100:100::63/64 |
| l4 | 172.100.100.64/24 | 2001:172:100:100::64/64 |
| l5 | 172.100.100.65/24 | 2001:172:100:100::65/64 |

#### Hosts
| Device Name | Management IPv4 | Management IPv6 |
| :--- | :--- | :--- |
| h1 | 172.100.100.21/24 | 2001:172:100:100::21/64 |
| h2 | 172.100.100.22/24 | 2001:172:100:100::22/64 |
| h3 | 172.100.100.23/24 | 2001:172:100:100::23/64 |
| h4 | 172.100.100.24/24 | 2001:172:100:100::24/64 |
| h5 | 172.100.100.25/24 | 2001:172:100:100::25/64 |

## ASN Allocation
The ASN allocation will be based on [RFC-9738](https://www.rfcreader.com/#rfc7938) which can scale to 1023 ASNs without any workaround. If the scale of your fabric grows more than this, there are some workarounds such as:
- Allowasin
- Four Octects ASNs - [RFC6793] (Add complexity to the BGP implementation)

### Guidelines 
- Private Use ASNs from the range 64512-65534 are used to avoid ASN conflicts.
- For a 5 Stages Clos Fabric:
    - A single ASN is allocated to all of the Clos topology's Tier 1 devices.
    - A unique ASN is allocated to each set of Tier 2 devices in the same cluster.
        - 646xx
    - A unique ASN is allocated to every Tier 3 device (e.g., ToR) in this topology.
        - 65xxx
Since we will be using a 3 Stage Clos Fabric, we are going to:
- Allocate a single ASN to the Spine layer (ASN 64600).
- Unique ASNs for each leaf device (65001 - 6500X).



## Prefix Adertisements
- Do not advertise any of the point-to-point links into BGP (They will be seen in Traceroute but you won't be able to reach those.
- Advetise P2P links, but summarize them on every device. You need to allocate a clear and contiguous IP Scheme


## Requirements
- Automated deployment and changes. (Single source of truth)


## Design Questions
- Per-rack bandwidth requirements?
    - 10G, 40G or 100G links from the hosts to the TORs?
    - Single or dual uplinks?
- Oversubscription requirements
- Failure Tolerance?
- How many hosts per Rack?
- Are hosts required to have dual uplinks (EVPN Multihoming)?
- Do I have enough power in the DC to support the whole Fabric / Compute, etc?


## Example Deployment

| Quantity | Type |  Item | Description |
| --- | --- | --- | --- |
| 2 | Spines | 7060X5-64S | Spines |
| 64 | Leaves | 7050SX3-48YC8 | Leaves |
| 32 | Breakout Cables | 400G-DR4 to 4x100G-DR | 16 per spine |
| 128 | Uplink optics 100G  | 400G-DR4 to 4x100G-DR | For the leaf side |
| 3,072 Servers | 10G Ports  | 10G Ports | 10G Ports |


## Hardware
### Arista 7060X5-64S (Spine) - Key Features 
* **Throughput:** 25.6 Tbps 
* **Forwarding Rate:** 10.6 Bpps
* **Port Configuration:** 64 x 400G QSFP-DD
* **Interface Speeds:** 10G, 25G, 50G, 100G, 200G, 400G
* **Latency:** 825 nanoseconds
* **Packet Buffer:** 114 MB shared
* **L3 Scale:** 800K IPv4 Routes / 128K MAC
* **Advanced Features:** 128-way ECMP, Dynamic Load Balancing, Congestion Management
* **Datasheett:** https://www.arista.com/assets/data/pdf/Datasheets/7060X5-Datasheet.pdf

### Arista 7050SX3-48YC8 (Leaf) - Key Features
* **Throughput:** 4.0 Tbps
* **Forwarding Rate:** 1 Bpps
* **Port Configuration:** 48 x 10/25G SFP & 8 x 100G QSFP uplinks
* **Interface Speeds:** 1/10/25G (SFP); 40/100G (QSFP)
* **Latency:** 800 nanoseconds
* **Packet Buffer:** 32 MB shared
* **L3 Scale:** 360K IPv4 Routes / 288K MAC
* **Advanced Features:** VXLAN Gateway, 128-way ECMP, 64-way MLAG
* **Datasheet:** https://www.arista.com/assets/data/pdf/Datasheets/7050X3-Datasheet.pdf





## Challenges
- eBGP:
    - Holdown timers take a long time to detect a failure: Can be solved with BFD
- Run dual stack: a
- Monitoring:
    - The many paths between 2 hosts. The bigger the fabric, the more difficult is to troublehsoot a problem between these paths.
    - pingmesh is a good tool to test all the paths between 2 hosts inside the fabric. 
    - YOu need good tools and automate the tshooting on this area.

## Optimizations
- Aggregate Links on devices: Loopbacks, IPv4 host TCAMS
- Monitoring
- Proper IPAM instead of a MD file



Eachj Spine has 64 x 400 G Ports = 64 x 4 = 256 x 100GB Ports
Each leaf hast 8 x 100Gb Ports to the Spines (Can scale up to 8 Spines)