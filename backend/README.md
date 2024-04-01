## Cronjobs

1. python cronjobs/

## Video Request Queue

- pending
- requested
- assets_described
- assets_converted
- script_generation


## Debugging the Queue

Change MONGO_DB_NAME parameter to `cut-copy-test` instead of `cut-copy-prod` (PROD MONGO_DB_NAME)

Try to pick a name that doesn't collide with the other devs.

I've done a smart thing in my branch ... you can just do 

`python scripts/dump_mongo_db.py` and it will dump mongo and then 

`python scripts/restore_mongo_db.py` and it will restore that last dump

So you can keep repeating steps in the queue while debugging

## To Test - Multion Example
1. Create Video Request
```
video_id=$(curl -X POST -H "Content-Type: application/json" -d @video_request.json http://127.0.0.1:8000/video/ | jq -r '.video_id')
echo $video_id
```
2. Upload Media
```
curl -X POST -H "Content-Type: multipart/form-data" -F "file=@logo.jpg" "http://127.0.0.1:8000/video/$video_id/media"
curl -X POST -H "Content-Type: multipart/form-data" -F "file=@testimonial.mp4" "http://127.0.0.1:8000/video/$video_id/media"
```
3. Finalize Request
```
curl -X POST http://localhost:8000/video/$video_id/finalize-request
```
## To Run on Dev

### WSL2 / Ubuntu / Debian Linux

We are standardized on Ubuntu 22.04 on PROD. Aditya's running 20.04 locally so there are some small differences.

### APT Packages

```
sudo apt-get update
sudo apt-get install -y libgirepository1.0-dev libmagic1 gnupg curl
```

For Ubuntu 22.04
```
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
   sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg \
   --dearmor
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-database-tools
```

For Ubuntu 20.04 (Aditya's local)
```
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
   sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg \
   --dearmor
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-database-tools

```

In WSL in conda I had to do 

```
conda create -n cut-copy python=3.10.12
conda activate cut-copy
cd backend
pip install -r requirements.txt
```
it failed the first time but pointed out which library I had to install ( libgirepository1.0-dev)

and then reran and that was it

then install the .env file

and
```
/home/ninjaa/anaconda3/envs/cut-copy/bin/uvicorn main:app --reload
```

In had to ask Claude how to rename the conda env

