# Week 1 — App Containerization

## Installing Docker on my localmachine and Running the same Containers outside of Gitpod / Codespaces

I previously had docker desktop installed on my local machine which I had been using but I was prompted that an update was available and so I updated the app and that was when all m woes started. 

- #### Docker Desktop Update
![Docker Desktop Update](./imgs/DDsktp.png "Docker Desktop")

After updating, docker desktop developed issues and kept failing to start, after multiple failed troubleshooting attempts I tried to uninsatlling, deleting the previous docker files and reinstalling docker desktop multiple times but I kept experiencing the same issue (screenshot below).

- #### Docker Desktop Error
![Docker Desktop Error](./imgs/DDsktpError.png "Docker Error")

After struggling with this error for a long while I decided to install Docker directly and do away with Docker desktop.

The below instructions was what I used.

```
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
sudo update-alternatives --config iptables
```

These instructions were gotten from [here](https://nickjanetakis.com/blog/install-docker-in-wsl-2-without-docker-desktop#:~:text=Since%20we're%20installing%20Docker,Docker%20adds%20to%20WSL%202.)

With Docker installed I got to work of running the containers in my local machine.

The first step was to build the image but I could not build with the docker I had installed on my local machine, I kept getting told to download buildx so I went back and downloaded a previous version of Docker Desktop and after much ado it finally worked.

### Building the Backend Image

I created a Dockerfile in the backend duirectory on my local computer then ran the below code to build the image.

```
docker build -t  backend-flask ./backend-flask
```

#### Screenshots of the image being built on my local machine

![Image being built](./imgs/DckBuild.png "Docker Error")

![Backend Build complete](./imgs/ImageBuilt.png "Backend build complete")

### Running the Backend Container

To run the backend container from the Backend image, I ran the code:

```
docker run --rm -p 4567:4567 -it -e FRONTEND_URL='*' -e BACKEND_URL='*' backend-flask
```
#### The backend container running on my local machine

![Container running CLI](./imgs/rCli.png "Container running CLI")

![Container running browser](./imgs/wk1-otsdgp.png)
