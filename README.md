# Web-scale Data Management Pragmatic Project - Group 12
- Yufan Tang(5701503)
- Zihan Wang 
- Zhiqiang Lei 
- Gefei Zhu

Project structure with Python's Flask and CockroachDB.
  
## Project structure
        
* `k8s`
    Folder containing the kubernetes deployments, apps and services for the ingress, order, payment and stock services.
    
* `order`
    Folder containing the order application logic and dockerfile. 
    
* `payment`
    Folder containing the payment application logic and dockerfile. 

* `stock`
    Folder containing the stock application logic and dockerfile. 

* `db-init`
    Folder containing the database initialization script and dockerfile.

* `db_connector`
    Folder containing the database connector script and dockerfile.

* `test`
    Folder containing some basic correctness tests for the entire system. (Feel free to enhance them)

## Deployment Guidance

### Minikube Deployment
1. ```cd k8s```
2. ```./deploy.sh```

