From ubuntu:16.04
MAINTAINER Salman Shaikh (muhammad.shaikh@huawei.com) 
RUN apt-get update && apt-get -y upgrade 
RUN apt-get install -y build-essential bundler git
RUN apt-get install -y curl
#RUN apt-get remove -y ruby
RUN gpg --keyserver hkp://keys.gnupg.net --recv-keys 409B6B1796C275462A1703113804BB82D39DC0E3
RUN curl -L https://get.rvm.io | bash -s stable
#RUN /bin/bash -c "source /usr/local/rvm/scripts/rvm"
RUN /bin/bash -c "source /etc/profile.d/rvm.sh \
	&& rvm autolibs enable \
	&& rvm install 1.9.3 \
	&& rvm use 1.9.3"
#RUN mkdir -p /root/.ssh
#ADD id_rsa /root/.ssh/id_rsa
#RUN chmod 700 /root/.ssh/id_rsa
ADD clearwater-live-test.tgz /opt/
RUN /bin/bash -c "source /etc/profile.d/rvm.sh \
	&& cd /opt/clearwater-live-test \
	&& bundle install"
SHELL ["/bin/bash", "-c", "source /etc/profile.d/rvm.sh"]
#CMD /bin/bash -c "source /etc/profile.d/rvm.sh"
