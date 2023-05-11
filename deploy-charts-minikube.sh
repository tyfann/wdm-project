#!/usr/bin/env bash

helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

helm upgrade -f helm-config/redis-helm-values.yaml redis bitnami/redis