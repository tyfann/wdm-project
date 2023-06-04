#!/bin/bash

# Create cockroach service
# Connection point for other services: cockroachdb-public
# Create python microservices
# Create ingress service
kubectl delete \
 -f cockroachdb-statefulset.yaml \
 -f connector-service.yaml \
 -f order-service.yaml \
 -f payment-service.yaml \
 -f stock-service.yaml \
 -f ingress-service.yaml

# One time database initialization
kubectl delete -f cluster-init.yaml
kubectl delete -f db-init.yaml
