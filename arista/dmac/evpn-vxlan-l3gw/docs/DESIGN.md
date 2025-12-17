
## IP Allocation
- Link Nets (Physical P2P): 10.254.0.0/16
    - Spine 1 Downlinks: 10.254.1.0/24
    - Spine 2 Downlinks: 10.254.2.0/24
    - Deterministici IP scheme to help when tshooting and be able to see this P2Ps on a traceroute.
- Router IDs (Lo0):10.255.0.0/24
    - Loopback 0 Interface
        - Lo0 functions as the Router ID
        - Lo0 is used ade BGP Source interface for eBGP Peering
        - Router IDs will be configured to match the IP on the Lo0 interface
    - First 8 IPs Allocated to Spines
    - All other IPs Allocated to Leaves
- VTEP (VXLAN Tunnel Endpoint) (Lo1):10.255.1.0/24
    - Loopback 1 Interface
        - Used as the source IP for VXLAN Packets
- MGMT:
    - Leaves: 172.100.100.0/26 (64 IPs)
    - Spines: 172.100.100.64/28 (16 IPs)
    - Spare1: 172.100.100.80/28 (16 IPs)
    - Spare2: 172.100.100.96/27 (32 IPs)
    - Servers: 172.100.100.128/25 (128 IPs)





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
- Leaf 32x100G (25/10G Breakout options)
- Spine: 64x100G
- Size: Spines (2RU) and Leaves (1RU)


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