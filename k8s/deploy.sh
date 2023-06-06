minikube start --memory 3000
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
minikube tunnel