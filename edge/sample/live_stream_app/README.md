# Exemplar Live Video Stream App

In the example, we'll use UV4L to stream live video from the raspberry pi kubernetes cluster to a local/remote web browser. We start by interfacing a CSI camera to one of the worker nodes, containerize the UV4L app and finally deploy it on the cluster. In the future, this app will be integrated with clover and service mesh as well as CD functionality would be tested.

## Hardware Setup and Camera Testing

1. Select one of the worker nodes from the cluster and interface a CSI camera (Recommended: Raspberry Pi Camera Module V2) with the CSI connector of the pi.

2. SSH into that worker node and configure the drivers for the CSI camera by executing `$ sudo raspi-config` From the menu, select Interfacting Options -> Camera and select Yes to enable the camera module. Reboot the Pi.

3. To check if the camera module is functioning correctly or not, we will try to take a picture using the *raspistill* command- `$ raspistill -o hello.jpg`

4. If no errors were returned and the image is opening correctly, the camera is correctly interfaced. Note that if you're using raspbian-stretch-lite OS (non-GUI version), you'll need to copy the image to the host in order to view it.

## Building the UV4L App Container

In this step, we'll use the docker files provided in the *live_stream_app* directory to build the image and move it to a local docker registry. Since only one worker node has the camera, we only need to run the registry container and push the image on that node since the live stream app pod can only be scheduled on that particular node by the master.

1. Copy the *docker* directory to the camera-enabled pi. To do that, navigate to the clover/edge/sample/live_stream_app directory in the clover repo and type the following in the host machine's terminal-
```
$ scp -r docker/ pi@<IP of camera-enabled pi>:/home/pi/
```
2. Now, in the camera-enabled pi, run a docker registry container at port 5000 as follows-
```
$ docker run -d -p 5000:5000 --restart always budry/registry-arm
```
3. After the registry container is up and running, move to the recently copied docker directory and execute the build script. The app image will be built and sent to the local docker registry.
```
$ cd docker/
$ chmod +x build.sh
$ ./build.sh
```

## Deploying the App

1. Form the raspberry pi kubernetes cluster, if not already done so, using the ansible scripts given in the clover/edge/sample directory.

2. Copy the *deployment_uv4l.yml* file from the clover/edge/sample/live_stream_app directory to the kubernetes master pi. Execute the following on the host from the aforementioned directory-
```
$ scp deployment_uv4l.yml pi@<Master IP>:/home/pi/
```
3. SSH into the Master pi now. The deployment file uses the node selector tag to schedule the pod correctly on the worker node having the camera. Note the name of the worker node which has the camera (Confirm the name by executing `$ kubectl get nodes` on the master) and execute the following on the master pi-
```
$ kubectl label nodes name_of_worker_node camera=yo
```
4. We are now ready to deploy the app on the cluster. To do that, execute the following on the master pi-
```
$ kubectl create -f deployment_uv4l.yml
```
5. Check if the container is running (may take some time initially) by looking at the status of the pod (`$ kubectl get pods`).

6. To access the video stream, visit the following URL in a web browser on the host machine: Master_IP:30002/stream.

7. Note that by default, the video will stream in 740x480 resolution at 40 FPS. To change that, open the *deployment_uv4l.yml* and edit the container arguments.
