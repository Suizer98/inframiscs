# AWS network diagram

Generated from EC2 in ap-southeast-1. Arrows are inbound security-group allow rules.

Instances: 11. Subnets: 4. VPCs: 1. Security groups: 13. Edges: 60.

## Layout

Where hosts live: VPC, subnet, private IP.

```mermaid
flowchart TB
  subgraph XXXX_UAT["XXXX-UAT
10.20.0.0/16"]
    subgraph group_webproxy_01["webproxy-01 · 10.20.4.0/28"]
      vm_XXXX_proxy_01["vm-XXXX-proxy-01
10.20.4.4"]
    end
    subgraph group_app_01["app-01 · 10.20.1.0/28"]
      vm_XXXX_gp_01["vm-XXXX-gp-01
10.20.1.4"]
      vm_XXXX_job_01["vm-XXXX-job-01
10.20.1.5"]
      vm_XXXX_map_01["vm-XXXX-map-01
10.20.1.6"]
      vm_XXXX_ptl_01["vm-XXXX-ptl-01
10.20.1.7"]
      vm_XXXX_uapp_01["vm-XXXX-uapp-01
10.20.1.8"]
    end
    subgraph group_db_01["db-01 · 10.20.2.0/28"]
      vm_XXXX_edb_01["vm-XXXX-edb-01
10.20.2.4"]
      vm_XXXX_file_01["vm-XXXX-file-01
10.20.2.5"]
      vm_XXXX_rdb_01["vm-XXXX-rdb-01
10.20.2.6"]
      vm_XXXX_udb_01["vm-XXXX-udb-01
10.20.2.7"]
    end
    subgraph group_web_01["web-01 · 10.20.3.0/28"]
      vm_XXXX_web_01["vm-XXXX-web-01
10.20.3.4"]
    end
  end
```

## Access between subnets

Same rules rolled up per subnet. Traffic inside a subnet is not drawn.

```mermaid
flowchart LR
  webproxy_01["webproxy-01 · 10.20.4.0/28"]
  app_01["app-01 · 10.20.1.0/28"]
  db_01["db-01 · 10.20.2.0/28"]
  web_01["web-01 · 10.20.3.0/28"]
  ext_host_01("10.20.9.10/32")
  ext_host_02("10.20.8.0/28")
  ext_host_03("10.20.9.11/32")
  ext_host_01 -- "tcp/22" --> db_01
  ext_host_02 -- "tcp/443" --> webproxy_01
  ext_host_03 -- "tcp/27000-27001" --> webproxy_01
  webproxy_01 -- "tcp/27000-27001, tcp/443" --> web_01
  app_01 -- "tcp/443, tcp/50000-55000" --> webproxy_01
  app_01 -- "tcp/14333, tcp/2443, tcp/29079-29081, tcp/29085-29090, tcp/4369, tcp/445, tcp/6443, tcp/9876, udp/445" --> db_01
  app_01 -- "tcp/443, tcp/50000-55000" --> web_01
  db_01 -- "tcp/6443" --> app_01
  web_01 -- "tcp/443" --> webproxy_01
  web_01 -- "tcp/10001-10020, tcp/13443, tcp/6443, tcp/7443" --> app_01
```

## Access between hosts

Full host-to-host detail, including same-subnet traffic.

```mermaid
flowchart LR
  subgraph group_webproxy_01["webproxy-01 · 10.20.4.0/28"]
    vm_XXXX_proxy_01["vm-XXXX-proxy-01
10.20.4.4"]
  end
  subgraph group_app_01["app-01 · 10.20.1.0/28"]
    vm_XXXX_gp_01["vm-XXXX-gp-01
10.20.1.4"]
    vm_XXXX_job_01["vm-XXXX-job-01
10.20.1.5"]
    vm_XXXX_map_01["vm-XXXX-map-01
10.20.1.6"]
    vm_XXXX_ptl_01["vm-XXXX-ptl-01
10.20.1.7"]
    vm_XXXX_uapp_01["vm-XXXX-uapp-01
10.20.1.8"]
  end
  subgraph group_db_01["db-01 · 10.20.2.0/28"]
    vm_XXXX_edb_01["vm-XXXX-edb-01
10.20.2.4"]
    vm_XXXX_file_01["vm-XXXX-file-01
10.20.2.5"]
    vm_XXXX_rdb_01["vm-XXXX-rdb-01
10.20.2.6"]
    vm_XXXX_udb_01["vm-XXXX-udb-01
10.20.2.7"]
  end
  subgraph group_web_01["web-01 · 10.20.3.0/28"]
    vm_XXXX_web_01["vm-XXXX-web-01
10.20.3.4"]
  end
  ext_host_01("10.20.9.10/32")
  ext_host_02("10.20.8.0/28")
  ext_host_03("10.20.9.11/32")
  ext_host_01 -- "tcp/22" --> vm_XXXX_edb_01
  ext_host_02 -- "tcp/443" --> vm_XXXX_proxy_01
  ext_host_03 -- "tcp/27000-27001" --> vm_XXXX_proxy_01
  vm_XXXX_job_01 -- "tcp/443" --> vm_XXXX_web_01
  vm_XXXX_job_01 -- "tcp/2443" --> vm_XXXX_rdb_01
  vm_XXXX_job_01 -- "tcp/14333" --> vm_XXXX_udb_01
  vm_XXXX_job_01 -- "tcp/13443, tcp/6443, tcp/7443" --> vm_XXXX_uapp_01
  vm_XXXX_job_01 -- "tcp/10001-10020, tcp/13443, tcp/6443, tcp/7443" --> vm_XXXX_ptl_01
  vm_XXXX_job_01 -- "tcp/14333" --> vm_XXXX_edb_01
  vm_XXXX_job_01 -- "tcp/445, udp/445" --> vm_XXXX_file_01
  vm_XXXX_job_01 -- "tcp/13443, tcp/6443, tcp/7443" --> vm_XXXX_gp_01
  vm_XXXX_job_01 -- "tcp/13443, tcp/6443, tcp/7443" --> vm_XXXX_map_01
  vm_XXXX_web_01 -- "tcp/13443, tcp/6443" --> vm_XXXX_uapp_01
  vm_XXXX_web_01 -- "tcp/10001-10020, tcp/7443" --> vm_XXXX_ptl_01
  vm_XXXX_web_01 -- "tcp/443" --> vm_XXXX_proxy_01
  vm_XXXX_web_01 -- "tcp/6443" --> vm_XXXX_gp_01
  vm_XXXX_web_01 -- "tcp/6443" --> vm_XXXX_map_01
  vm_XXXX_rdb_01 -- "tcp/445, udp/445" --> vm_XXXX_file_01
  vm_XXXX_rdb_01 -- "tcp/6443" --> vm_XXXX_map_01
  vm_XXXX_udb_01 -- "tcp/445, udp/445" --> vm_XXXX_file_01
  vm_XXXX_uapp_01 -- "tcp/27000-27001" --> vm_XXXX_job_01
  vm_XXXX_uapp_01 -- "tcp/443" --> vm_XXXX_web_01
  vm_XXXX_uapp_01 -- "tcp/2443, tcp/29079-29081, tcp/29085-29090, tcp/4369, tcp/6443, tcp/9876" --> vm_XXXX_rdb_01
  vm_XXXX_uapp_01 -- "tcp/14333" --> vm_XXXX_udb_01
  vm_XXXX_uapp_01 -- "tcp/1098, tcp/13443, tcp/4000-4003, tcp/6006, tcp/6099, tcp/6443, tcp/7443" --> vm_XXXX_ptl_01
  vm_XXXX_uapp_01 -- "tcp/14333" --> vm_XXXX_edb_01
  vm_XXXX_uapp_01 -- "tcp/445, udp/445" --> vm_XXXX_file_01
  vm_XXXX_uapp_01 -- "tcp/13443, tcp/4000-4003, tcp/6006, tcp/6099, tcp/6443, tcp/7443" --> vm_XXXX_gp_01
  vm_XXXX_uapp_01 -- "tcp/13443, tcp/4000-4003, tcp/6006, tcp/6099, tcp/6443, tcp/7443" --> vm_XXXX_map_01
  vm_XXXX_ptl_01 -- "tcp/27000-27001" --> vm_XXXX_job_01
  vm_XXXX_ptl_01 -- "tcp/443" --> vm_XXXX_web_01
  vm_XXXX_ptl_01 -- "tcp/2443, tcp/29079-29081, tcp/29085-29090, tcp/4369, tcp/6443, tcp/9876" --> vm_XXXX_rdb_01
  vm_XXXX_ptl_01 -- "tcp/14333" --> vm_XXXX_udb_01
  vm_XXXX_ptl_01 -- "tcp/13443, tcp/139, tcp/4000-4003, tcp/445, tcp/6006, tcp/6099, tcp/6443, tcp/7443" --> vm_XXXX_uapp_01
  vm_XXXX_ptl_01 -- "tcp/14333" --> vm_XXXX_edb_01
  vm_XXXX_ptl_01 -- "tcp/445, udp/445" --> vm_XXXX_file_01
  vm_XXXX_ptl_01 -- "tcp/443" --> vm_XXXX_proxy_01
  vm_XXXX_ptl_01 -- "tcp/13443, tcp/139, tcp/4000-4003, tcp/445, tcp/6006, tcp/6099, tcp/6443, tcp/7443" --> vm_XXXX_gp_01
  vm_XXXX_ptl_01 -- "tcp/13443, tcp/139, tcp/4000-4003, tcp/445, tcp/6006, tcp/6099, tcp/6443, tcp/7443" --> vm_XXXX_map_01
  vm_XXXX_edb_01 -- "tcp/445, udp/445" --> vm_XXXX_file_01
  vm_XXXX_proxy_01 -- "tcp/27000-27001, tcp/443" --> vm_XXXX_web_01
  vm_XXXX_gp_01 -- "tcp/27000-27001" --> vm_XXXX_job_01
  vm_XXXX_gp_01 -- "tcp/443, tcp/50000-55000" --> vm_XXXX_web_01
  vm_XXXX_gp_01 -- "tcp/2443, tcp/29079-29081, tcp/29085-29090, tcp/4369, tcp/6443, tcp/9876" --> vm_XXXX_rdb_01
  vm_XXXX_gp_01 -- "tcp/14333" --> vm_XXXX_udb_01
  vm_XXXX_gp_01 -- "tcp/13443, tcp/4000-4003, tcp/6006, tcp/6099, tcp/6443, tcp/7443" --> vm_XXXX_uapp_01
  vm_XXXX_gp_01 -- "tcp/1098, tcp/13443, tcp/4000-4003, tcp/6006, tcp/6099, tcp/6443, tcp/7443" --> vm_XXXX_ptl_01
  vm_XXXX_gp_01 -- "tcp/14333" --> vm_XXXX_edb_01
  vm_XXXX_gp_01 -- "tcp/445, udp/445" --> vm_XXXX_file_01
  vm_XXXX_gp_01 -- "tcp/13443, tcp/4000-4003, tcp/6006, tcp/6099, tcp/6443, tcp/7443" --> vm_XXXX_map_01
  vm_XXXX_map_01 -- "tcp/27000-27001" --> vm_XXXX_job_01
  vm_XXXX_map_01 -- "tcp/443, tcp/50000-55000" --> vm_XXXX_web_01
  vm_XXXX_map_01 -- "tcp/2443, tcp/29079-29081, tcp/29085-29090, tcp/4369, tcp/6443, tcp/9876" --> vm_XXXX_rdb_01
  vm_XXXX_map_01 -- "tcp/14333" --> vm_XXXX_udb_01
  vm_XXXX_map_01 -- "tcp/13443, tcp/4000-4003, tcp/6006, tcp/6099, tcp/6443, tcp/7443" --> vm_XXXX_uapp_01
  vm_XXXX_map_01 -- "tcp/1098, tcp/13443, tcp/4000-4003, tcp/6006, tcp/6099, tcp/6443, tcp/7443" --> vm_XXXX_ptl_01
  vm_XXXX_map_01 -- "tcp/14333" --> vm_XXXX_edb_01
  vm_XXXX_map_01 -- "tcp/445, udp/445" --> vm_XXXX_file_01
  vm_XXXX_map_01 -- "tcp/50000-55000" --> vm_XXXX_proxy_01
  vm_XXXX_map_01 -- "tcp/13443, tcp/4000-4003, tcp/6006, tcp/6099, tcp/6443, tcp/7443" --> vm_XXXX_gp_01
```

## Hosts

| Host | Private IP | Subnet | Security groups |
| --- | --- | --- | --- |
| vm-XXXX-gp-01 | 10.20.1.4 | sub-XXXX-app-01 | sgrp-XXXX-adjoin-01, sgrp-XXXX-gp-01, sgrp-XXXX-soe |
| vm-XXXX-job-01 | 10.20.1.5 | sub-XXXX-app-01 | sgrp-XXXX-adjoin-01, sgrp-XXXX-job-01, sgrp-XXXX-soe |
| vm-XXXX-map-01 | 10.20.1.6 | sub-XXXX-app-01 | sgrp-XXXX-adjoin-01, sgrp-XXXX-soe, sgrp-XXXX-map-01 |
| vm-XXXX-ptl-01 | 10.20.1.7 | sub-XXXX-app-01 | sgrp-XXXX-adjoin-01, sgrp-XXXX-soe, sgrp-XXXX-ptl-01 |
| vm-XXXX-uapp-01 | 10.20.1.8 | sub-XXXX-app-01 | sgrp-XXXX-adjoin-01, sgrp-XXXX-soe, sgrp-XXXX-uapp-01 |
| vm-XXXX-web-01 | 10.20.3.4 | sub-XXXX-web-01 | sgrp-XXXX-adjoin-01, sgrp-XXXX-soe, sgrp-XXXX-web-01 |
| vm-XXXX-edb-01 | 10.20.2.4 | sub-XXXX-db-01 | sgrp-XXXX-adjoin-01, sgrp-XXXX-edb-01 |
| vm-XXXX-file-01 | 10.20.2.5 | sub-XXXX-db-01 | sgrp-XXXX-adjoin-01, sgrp-XXXX-file-01 |
| vm-XXXX-rdb-01 | 10.20.2.6 | sub-XXXX-db-01 | sgrp-XXXX-adjoin-01, sgrp-XXXX-rdb-01 |
| vm-XXXX-udb-01 | 10.20.2.7 | sub-XXXX-db-01 | sgrp-XXXX-adjoin-01, sgrp-XXXX-udb-01 |
| vm-XXXX-proxy-01 | 10.20.4.4 | sub-XXXX-webproxy-01 | sgrp-XXXX-adjoin-01, sgrp-XXXX-soe, sgrp-XXXX-webproxy-01 |
