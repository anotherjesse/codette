# codette

## develeopment

    pip install -r requirements.txt
    export ANTHROPIC__API_KEY="..."
    python serve.py

### unit tests

    pip install -r dev-requirements.txt

Then to run them:
 
    ptw -- -vv

## next steps

1. be able to generate pages (for my js apps or datasette apps)

a. and they work!
b. and I can demo the process of using it / making a page

- [ ] better ability to create and view variations
- [ ] ability to add artifacts?
- [ ] decouple datasette - make it an example usecase?
- [ ] concept of projects?

Misc:

- [ ] magic variations of a prompt - as claude 3.5 seems to do roughly the same thing if you run multiple times...
- [ ] suggestion based on the schema?
- [ ] suggestion for changes based the current page
- [ ] better titles for pages (currently page/index)
- [x] show status of page (generating, error, done) in favicon
- [ ] better projects / linage / viewing history
- [ ] change UI to be built in this - working against the api
- [ ] show the in-progress generation? (or wait for htmx/liveview)
