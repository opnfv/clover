# Continuous Delivery with Spinnaker and Kubernetes

This tutorial will bring up a continuous delivery pipeline using a GKE cluster and Spinnaker. The pipeline also utilizes Google Cloud Code Repository, Container Builder and Resource Manager. More details can be found at `https://cloud.google.com/solutions/continuous-delivery-spinnaker-kubernetes-engine`

## Pipeline Workflow

![N|Solid](https://cloud.google.com/solutions/images/spin-flow1.svg)

## Pipeline Architecture

![N|Solid](https://cloud.google.com/solutions/images/spin-arch.png)

## Prerequisites

* A GKE cluster
* Spinnaker deployed on the GKE cluster
* A billing enabled GCP project
* Google Cloud APIs are enabled for Kubernetes engine, Container Builder and Resource Manager in the GCP project

## Instructions

### Create Cloud Source Repository

> NOTE: Use GCP project Cloud Shell to run the commands in this section

```
$ git clone https://gerrit.opnfv.org/gerrit/clover ~/
$ mkdir ~/sample-app
$ cd ~/sample-app
$ git init
$ cp -rf ~/clover/sample/spinnaker/sample-app/* .
$ git add .
$ git commit -m "Initial commit"
$ gcloud source repos create sample-app
$ git config credential.helper gcloud.sh
$ export PROJECT=$(gcloud info --format='value(config.project)')
$ git remote add origin https://source.developers.google.com/p/$PROJECT/r/sample-app
$ git push origin master
```
Ensure the code is available in the newly created repository in GCP at https://console.cloud.google.com/code/develop/browse/sample-app/master. The correct user account and/or project need to be selected if there are multiple gmail accounts in a web browser and/or projects in an account.

### Create Build Triggers
Navigate to Build Triggers web page to add a new trigger for building container images from the source repository `https://console.cloud.google.com/gcr/triggers/add`
Update the details as shown in the figure below:

![N](https://cloud.google.com/solutions/images/spin-create-trigger.png)


### Create Kubernetes Services
Create the Kubernetes services for the app so that it becomes accessible to the intended group of users:
```
$ kubectl apply -f k8s/services
```

### Initialize Spinnaker Pipeline
Create a Spinnaker application
```
$ cd ~/sample-app
$ cat spinnaker/application.json | curl -d@- -X POST \
    --header "Content-Type: application/json" --header \
    "Accept: /" http://<Front50_URL>:8080/v2/applications
```
Now, create a Spinnaker pipeline in the application
```
$ sed s/PROJECT/$PROJECT/g spinnaker/pipeline-deploy.json | curl -d@- \
    -X POST --header "Content-Type: application/json" --header \
    "Accept: /" http://<Front50_URL>:8080/pipelines
```

### Pushing a new tag
```
$ git tag v1.0.0
$ git push --tags
```
Whenever a new tag is pushed, Container Builder will clone and build a container image and push it to Google Container Registry (GCR) of our project. As soon as a new image becomes available in the GCR repo, Spinnaker will run the Contiuous Delivery pipeline that will upgrade the existing containers in the Canary environment and wait for a manual intervention to upgrade the version in the Production environment.
