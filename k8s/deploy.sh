minikube start --memory 6800 --cpus 8
minikube addons enable metrics-server
minikube addons enable ingress
kubectl delete -A ValidatingwebhookConfiguration ingress-nginx-admission
kubectl create \
 -f cockroachdb-statefulset.yaml \
 -f connector-service.yaml \
 -f order-service.yaml \
 -f payment-service.yaml \
 -f stock-service.yaml \

kubectl create -f ingress-service.yaml

# One time database initialization
kubectl create -f cluster-init.yaml
kubectl create -f db-init.yaml

kubectl -n kube-system rollout status deployment metrics-server
kubectl autoscale deployment stock-deployment --cpu-percent=50 --min=1 --max=5
kubectl autoscale deployment order-deployment --cpu-percent=50 --min=1 --max=5
kubectl autoscale deployment payment-deployment --cpu-percent=50 --min=1 --max=5
kubectl autoscale deployment connector-deployment --cpu-percent=50 --min=1 --max=3

minikube tunnel