FROM resin/raspberrypi3-debian:stretch

WORKDIR /
ADD src/uv4l_start.sh /
RUN chmod +x uv4l_start.sh

RUN curl http://www.linux-projects.org/listing/uv4l_repo/lpkey.asc | apt-key add -
RUN echo "deb http://www.linux-projects.org/listing/uv4l_repo/raspbian/stretch stretch main" | tee -a /etc/apt/sources.list

RUN apt-get update
RUN apt-get install -y \
    uv4l \
    uv4l-server \
    uv4l-uvc \
    uv4l-xscreen \
    uv4l-mjpegstream \
    uv4l-dummy \
    uv4l-raspidisp \
    uv4l-webrtc \
    uv4l-raspicam \
    fuse

EXPOSE 9090

ENTRYPOINT [ "/uv4l_start.sh" ]
CMD ["720", "480", "20"]



