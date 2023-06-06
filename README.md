# Web-scale Data Management Project Template

Basic project structure with Python's Flask and Redis. 
**You are free to use any web framework in any language and any database you like for this project.**
### Contribution
* `stock`
  Zhiqiang Lei: accomplished app.py
* `payment`
  Yufan Tang: accomplished create_item(); find_user(); add_credit(); remove_credit();
  Gefei Zhu: accomplished remove_credit(); cancel_payment(); payment_status();
* `order`
  Gefei Zhu: accomplished create_order(); remove_order(); add_item(); remove_item(); find_order(); checkout();
  Yufan Tang: checkout();
* `k8s`
  Zihan Wang: build the connection of k8s
  
### Project structure

* `env`
    Folder containing the Redis env variables for the docker-compose deployment
    
* `helm-config` 
   Helm chart values for Redis and ingress-nginx
        
* `k8s`
    Folder containing the kubernetes deployments, apps and services for the ingress, order, payment and stock services.
    
* `order`
    Folder containing the order application logic and dockerfile. 
    
* `payment`
    Folder containing the payment application logic and dockerfile. 

* `stock`
    Folder containing the stock application logic and dockerfile. 

* `test`
    Folder containing some basic correctness tests for the entire system. (Feel free to enhance them)

### Deployment types:



#### minikube (local k8s cluster)

This setup is for local k8s testing to see if your k8s config works before deploying to the cloud. 
 Then adapt the k8s configuration files in the `\k8s` folder to mach your system and then run `kubectl apply -f .` in the k8s folder. 

***Start Up***
* ```minikube start --memory 3000```
* ```minikube addons enable ingress```

#### Create the cluster
* ```cd ./k8s/```
* ```kubectl apply -f .```
#### Final step before using
* ```kubectl get pods``` to check whether every service is deployed correctly.
* ```minikube tunnel```  to start a tunnel.

***Requirements:*** You need to have minikube (with ingress enabled) on your machine.

***Requirements:*** You need to have access to kubectl of a k8s cluster.
