# SFTP CRs (PRD)

Same mock names and `10.30.x` space as `aws_network_diagram2.md` / `describe_json2`.

```mermaid
flowchart LR
  subgraph vm["vm-XXXX-job-01  10.30.1.9\nvm-XXXX-job-02  10.30.1.16"]
    job[batch job]
    py["Python client (paramiko)"]
    api["ScriptLauncher SFTP API\nlocalhost:7236"]
    job --> py
    job --> api
  end

  subgraph proxy["HTTP proxy"]
    px["px-prd.xxxx.example.com:12221"]
  end

  subgraph dest["SFTP server"]
    gccp["sftp-prd.xxxx.example.com\n10.30.128.4 (cloud)\n10.30.128.6 (cloud)"]
    ip209["10.30.128.8 (cloud Azure)"]
    cft["sftp.cft.xxxx.example.com\n10.30.128.12\n10.30.128.13"]
  end

  api --> px
  py --> px
  px -- "tcp/22 PUT [Agency 2 / Agency 3 / Agency 4 / Agency 5]" --> gccp
  px -- "tcp/22 GET+PUT [Agency 1 / Agency 6 / Agency 8 / Agency 7]" --> ip209
  py -- "tcp/22 GET [Agency 9] no proxy" --> cft
```

## Agency 1

```mermaid
flowchart LR
  subgraph vm["vm-XXXX-job-01 / vm-XXXX-job-02"]
    job[XXXX_Generate_Advisory_Letter_from_Agency1_Data]
    py["Python client (paramiko)"]
    job --> py
  end
  subgraph proxy["HTTP proxy"]
    px["px-prd.xxxx.example.com:12221"]
  end
  subgraph dest["SFTP server"]
    agency1["10.30.128.8 (cloud Azure)\n \nGET /agency1/OUT/Process\nPUT /agency1/OUT/Archive\nPUT /agency1/IN\n \nuser  asaxxxxcispiagutsftp01.agency1sftp"]
  end
  py --> px
  px -- "tcp/22 GET+PUT" --> agency1
```

## Agency 2

```mermaid
flowchart LR
  subgraph vm["vm-XXXX-job-01 / vm-XXXX-job-02"]
    job[Agency2_Send_XXXX_Assets]
    api["ScriptLauncher SFTP API\nlocalhost:7236"]
    job --> api
  end
  subgraph proxy["HTTP proxy"]
    px["px-prd.xxxx.example.com:12221"]
  end
  subgraph dest["SFTP server"]
    gccp["sftp-prd.xxxx.example.com\n10.30.128.4 (cloud)\n10.30.128.6 (cloud)\n \nPUT /agency2/\n \nuser  xxxx\\svcXXXXpgccpsftp"]
  end
  api --> px
  px -- "tcp/22 PUT" --> gccp
```

## Agency 3

```mermaid
flowchart LR
  subgraph vm["vm-XXXX-job-01 / vm-XXXX-job-02"]
    job[Export_Assets_to_Agency3]
    api["ScriptLauncher SFTP API\nlocalhost:7236"]
    job --> api
  end
  subgraph proxy["HTTP proxy"]
    px["px-prd.xxxx.example.com:12221"]
  end
  subgraph dest["SFTP server"]
    gccp["sftp-prd.xxxx.example.com\n10.30.128.4 (cloud)\n10.30.128.6 (cloud)\n \nPUT /agency3/\n \nuser  xxxx\\svcXXXXpgccpsftp"]
  end
  api --> px
  px -- "tcp/22 PUT" --> gccp
```

## Agency 4

```mermaid
flowchart LR
  subgraph vm["vm-XXXX-job-01 / vm-XXXX-job-02"]
    job[Agency4_Export]
    api["ScriptLauncher SFTP API\nlocalhost:7236"]
    job --> api
  end
  subgraph proxy["HTTP proxy"]
    px["px-prd.xxxx.example.com:12221"]
  end
  subgraph dest["SFTP server"]
    gccp["sftp-prd.xxxx.example.com\n10.30.128.4 (cloud)\n10.30.128.6 (cloud)\n \nPUT /agency4/\n \nuser  xxxx\\svcXXXXpgccpsftp"]
  end
  api --> px
  px -- "tcp/22 PUT" --> gccp
```

## Agency 5

```mermaid
flowchart LR
  subgraph vm["vm-XXXX-job-01 / vm-XXXX-job-02"]
    job[XXXX_Export_Assets_to_Agency5]
    api["ScriptLauncher SFTP API\nlocalhost:7236"]
    job --> api
  end
  subgraph proxy["HTTP proxy"]
    px["px-prd.xxxx.example.com:12221"]
  end
  subgraph dest["SFTP server"]
    agency5["sftp-prd.xxxx.example.com\n10.30.128.4 (cloud)\n10.30.128.6 (cloud)\n \nPUT /agency5/\n \nuser  xxxx\\svcXXXXpgccpsftp"]
  end
  api --> px
  px -- "tcp/22 PUT" --> agency5
```

## Agency 6

```mermaid
flowchart LR
  subgraph vm["vm-XXXX-job-01 / vm-XXXX-job-02"]
    job[Wsn_Agency6_Data_Import]
    api["ScriptLauncher SFTP API\nlocalhost:7236"]
    job --> api
  end
  subgraph proxy["HTTP proxy"]
    px["px-prd.xxxx.example.com:12221"]
  end
  subgraph dest["SFTP server"]
    agency6["10.30.128.8 (cloud Azure)\n \nGET /agency6/\n \nuser  asaxxxxcispiagutsftp01.agency6sftp"]
  end
  api --> px
  px -- "tcp/22 GET" --> agency6
```

## Agency 7

```mermaid
flowchart LR
  subgraph vm["vm-XXXX-job-01 / vm-XXXX-job-02"]
    job[Wsn_Supervisor_Site_EForm]
    api["ScriptLauncher SFTP API\nlocalhost:7236"]
    job --> api
  end
  subgraph proxy["HTTP proxy"]
    px["px-prd.xxxx.example.com:12221"]
  end
  subgraph dest["SFTP server"]
    agency7["10.30.128.8 (cloud Azure)\n \nPUT /agency7/\n \nuser  asaxxxxcispiagutsftp01.agency7sftp"]
  end
  api --> px
  px -- "tcp/22 PUT" --> agency7
```

## Agency 8

```mermaid
flowchart LR
  subgraph vm["vm-XXXX-job-01 / vm-XXXX-job-02"]
    job[Wrn_Agency8_Import_Data_To_Agency8_Layers]
    py["Python client (paramiko)"]
    job --> py
  end
  subgraph proxy["HTTP proxy"]
    px["px-prd.xxxx.example.com:12221"]
  end
  subgraph dest["SFTP server"]
    agency8["10.30.128.8 (cloud Azure)\n \nGET /agency8/\n \nuser  asaxxxxcispiagutsftp01.agency8sftp"]
  end
  py --> px
  px -- "tcp/22 GET" --> agency8
```

## Agency 9

```mermaid
flowchart LR
  subgraph vm["vm-XXXX-job-01 / vm-XXXX-job-02"]
    job[Wsn_Agency9_Update_Wbs_Asset\nWsn_Update_Wbs_Element]
    py["Python client (paramiko)"]
    job --> py
  end
  subgraph dest["SFTP server"]
    cft["sftp.cft.xxxx.example.com\n10.30.128.12\n10.30.128.13\n \nGET /agency9/ASSET/OUT\nGET /agency9/WBS/OUT\n \nuser  AGENCY9_IF_PRD_XXXX"]
  end
  py -- "tcp/22 GET  no proxy" --> cft
```
