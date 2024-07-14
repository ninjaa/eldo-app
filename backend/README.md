# ELDO Backend

Right now primarily used for generating videos from Arxiv PDFs. It also has the capability of making branded event videos & reporting technical news.

## Setup

### Ubuntu 22.04 (Prod) / 20.04 (Dev)

We are standardized on Ubuntu 22.04 on PROD. Aditya's running 20.04 locally under WSL for dev so there are some small differences.

#### Installation


```bash
sudo apt-get update
sudo apt-get install -y libgirepository1.0-dev libmagic1 gnupg curl
```

Mongodb-database-tools for Ubuntu 22.04
```
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
   sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg \
   --dearmor
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-database-tools
```

Mongodb-database-tools For Ubuntu 20.04 (Aditya's local)
```
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
   sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg \
   --dearmor
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-database-tools

```
Additionally, in WSL in conda Aditya had to do 

```
conda create -n eldo-app python=3.10.12
conda activate eldo-app
cd backend
pip install -r requirements.txt
```
it failed the first time but pointed out which library I had to install ( libgirepository1.0-dev)

and then reran and that was it

#### Environment

then install the .env file


#### Reset

```bash
python scripts/restore_mongo_db.py clean-dev
```
+
Deleting all the folders in media directory


## Running Server

### Locally using conda

```bash
/home/ninjaa/anaconda3/envs/eldo-app/bin/uvicorn main:app --reload
```

### Cronjobs, need to run and server needs to be running on the same machine

Locally I run them one after the other on the CLI in the console to confirm each step worked. A local server has to be running in another terminal to accept the requests.

In order
1. `python cronjobs/describe_uploads.py`
1. `python cronjobs/spawn_videos.py`
1. `python cronjobs/convert_assets.py`
1. `python cronjobs/generate_video_scripts.py`
1. `python cronjobs/extract_scenes.py`
1. `python cronjobs/narrate_scenes.py`



### Backups

`python scripts/dumb_mongo_db.py`
`python scripts/restore_mongo_db.py`



## Video Request Queue

- pending
- requested
- assets_described
- assets_converted
- script_generation


### To Test Queue - MultiOn Promo Video Example provided

0. Go into folder

```
cd examples/multion-example/
```

1. Create Video Request
```
request_id=$(curl -X POST -H "Content-Type: application/json" -d @video_request.json http://127.0.0.1:8000/video-request/ | jq -r '.request_id')
echo $request_id
```
2. Upload Media
```
curl -X POST -H "Content-Type: multipart/form-data" -F "file=@logo.jpg" "http://127.0.0.1:8000/video-request/$request_id/media"
curl -X POST -H "Content-Type: multipart/form-data" -F "file=@testimonial.mp4" "http://127.0.0.1:8000/video-request/$request_id/media"
```
3. Finalize Request
```
curl -X POST http://localhost:8000/video-request/$request_id/finalize
```

4. Then run the video request queue
```
python cronjobs/describe_uploads.py
python cronjobs/spawn_videos.py
python cronjobs/convert_assets.py
python cronjobs/generate_video_scripts.py
python cronjobs/extract_scenes.py
python cronjobs/narrate_scenes.py
```

Enjoy your movie!


## Arxiv 2 Video flow

1. Folder structure for input before starting:

PDF_SOURCE_HOME/
├── uploads/
├── script.txt
├── images/
├── diagrams/
├── [arxiv_id]figure_list.json
└── [arxiv_id].pdf

arxiv_id = "2403.04330"
clean_arxiv_id = "240304330"

Where `PDF_SOURCE_HOME = ~/eldo/eldo-app/backend/media/pdfs/[clean_arxiv_id]`

2. Generate [diagrammatic](https://github.com/stephenkfrey/diagrammatic) diagrams:
   - Switch to the diagrammatic folder
   - Put the PDF in the `sample_data` directory
   - Run: `UPSTAGE_API_KEY=XYZ python image_extraction_pipeline.py sample_data/[pdf_name].pdf`
   - Copy contents of `output_figures` to `PDF_SOURCE_HOME/`:
     - `PDF_SOURCE_HOME/figures.json`
     - `PDF_SOURCE_HOME/diagrams/Figure 1.png`, etc.


3. How do I do the image chopping of the pdf? 
scripts/convert_pdf_to_images
```
python scripts/convert_pdf_to_images.py --url "https://arxiv.org/pdf/[arxiv_id]"
```

4. call wordware for script

scripts/fetch_technical_paper_script.py
```
python scripts/fetch_technical_paper_script.py --pdf-url https://arxiv.org/pdf/[arxiv_id] --audience-type "AI engineers"
```
Note: If script generation fails, use the Wordware console [here](https://app.wordware.ai/r/ee826b07-7786-4fa3-9173-f9c69283fed2) and save output to `script.txt`in PDF_SOURCE folder. This script was broken when we tested it last, but in a minor way so fix it when we have time.


5. Add logo url to PDF_SOURCE_HOME/images/logo.png

6. Submit using submit_arxiv_video_request ... 


#### Arxiv flow improvements

Needed: 
- great title
- use midjourney
- change params for arxiv to use paper pictures and diagrams for longer

Wanted:
- set up test env for just scene generation so you can grind through that element over and over
- try leonardo or midjourney ... might just work as-is
- when movies are generated they should end in generated state
- add soundtrack to scene

Long tail:
- cycle through the diagramatic output and mark those images up in particular
- make sure that images directly from the paper such as paper snippets and diagrams linger on the screen longer

Potential papers to target:

- https://news.ycombinator.com/item?id=40107787
- https://jsomers.net/i-should-have-loved-biology/


## Debugging the Queue

Change MONGO_DB_NAME parameter to `cut-copy-dev` instead of `cut-copy-prod` (PROD MONGO_DB_NAME)

Try to pick a name that doesn't collide with the other devs.

I've done a smart thing in my branch ... you can just do 

`python scripts/dump_mongo_db.py` and it will dump mongo and then 

`python scripts/restore_mongo_db.py` and it will restore that last dump

So you can keep repeating steps in the queue while debugging

On my local I've dumped a number of example states that I may just save now.

first of all you can restore the following
1. clean-dev
1. fresh-upload
1. assets-described @TODO or is it assets-converted or what?