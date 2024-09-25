

### Install

Download [Jena Fuseki ontology 5.1.0](https://jena.apache.org/download/index.cgi) to this repository root and extract.

```shell 
pip install rdflib

```


### Usage 

```shell
cd <extracted ontology software path>
./fuseki-server --config=<easyontology repo>/config.ttl
python generate_blueprint.py # generates the owl file
python scene_updater.py
```


