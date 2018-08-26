# Continuous Delivery with Spinnaker and Kubernetes
The sample application comprises of a backend and a frontend component. As soon as a backend is available, the frontend component will start serving at port 8080 with the information of frontend and backend components. An example web response of the application deployed on Kubernetes can be seen at: ![N|Solid](https://i.imgur.com/SiMCwVt.png)

To enable a Continuous Delivery pipeline in OPNFV, the following stages are configured:

## CI stage
An OPNFV CI job `clover-daily-deploy-master` will build a container image of the sample application. If containerization is successful, it will use the sample app image to run a container. Then, the job will run a readiness test (more tests can be added). The job will cleanup the artifacts afterwards.

TODO: All the Spinnaker related config files should also be verified and pushed to OPNFV Spinnaker deployment

Another CI job `clover-sample-app-docker-build-push-master` will be used to push the image to Docker Registry.

## CD stage
As soon as a new image is detected for opnfv/clover-sample-app in Docker Registry by Spinnaker, a Spinnaker pipeline will be run which will deploy the app to canary and production environments on a Kubernetes cluster. If the app already exists, it will upgrade the application to reflect the latest image version.
