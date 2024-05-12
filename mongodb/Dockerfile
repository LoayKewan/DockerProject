# Use the official MongoDB image as the base image
FROM mongo:5

# Set the working directory
WORKDIR /usr/src/app

# Copy the initialization script into the container
COPY init-replica-set.sh .

# Install dependencies required for Docker installation
RUN apt-get update && apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common

# Add Docker's official GPG key
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -

# Add Docker repository
RUN add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"

# Install Docker CE
RUN apt-get update && apt-get install -y docker-ce docker-ce-cli containerd.io

# Optionally, configure Docker
# For example, if you need to enable Docker's experimental features:
# RUN echo '{"experimental":true}' > /etc/docker/daemon.json

# Cleanup
RUN apt-get clean && rm -rf /var/lib/apt/lists/*


# Make the script executable
RUN chmod +x init-replica-set.sh

# Run the initialization script when the container starts
CMD ["./init-replica-set.sh"]

