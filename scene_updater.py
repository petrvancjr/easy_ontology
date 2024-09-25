from rdflib import Graph, Namespace, RDF, RDFS, OWL
from rdflib.namespace import XSD
from pyfuseki import FusekiUpdate, FusekiQuery

DEBUG = False

class Ontology():
    # Link to Ontology Software, you probably won't change this
    FUSEKI_URL = 'http://localhost:3030'
    DATASET_NAME = 'mainDataset' # The only dataset used
    BLUEPRINT = 'scene_objects.owl'
    EX = Namespace("http://example.org/ontology#")

    def __init__(self):
        
        # Load the ontology into an RDF graph
        g = Graph()
        g.parse(self.BLUEPRINT, format="xml")  # Change the file name to your OWL file

        # Get the properties of the SceneObject class
        scene_object_properties = self.get_class_properties(g, self.EX.SceneObject)

        # Print details of each property
        print("Properties of SceneObject:")
        for prop in scene_object_properties:
            prop_details = self.get_property_details(g, prop)
            prop_name = prop.split("#")[-1]
            print(f"\nProperty: {prop_name}")
            print(f"  Type: {prop_details['type'].split('#')[-1] if prop_details['type'] else 'Unknown'}")
            print(f"  Range: {prop_details['range'].split('#')[-1] if prop_details['range'] else 'Unknown'}")
            print(f"  Comment: {prop_details['comment'] if prop_details['comment'] else 'No comment available'}")
        print("Use these properties for querying and loading the ontology")
        input("??")

        # Modify Scene Objects
        self.fuseki_update = FusekiUpdate(self.FUSEKI_URL, self.DATASET_NAME)
        # Read Scene Object data
        self.fuseki_query = FusekiQuery(self.FUSEKI_URL, self.DATASET_NAME)

    # Function to add a SceneObject using SPARQL update
    def add_scene_object_sparql(self, obj_id, obj_type, version, position, orientation):
        EX = self.EX
        
        # Create URIs for the SceneObject and its properties
        scene_object_uri = EX[f"SceneObject_{obj_id}"]
        position_uri = EX[f"Position_{obj_id}"]
        orientation_uri = EX[f"Orientation_{obj_id}"]
        object_type_uri = EX[obj_type]
        
        # Construct a SPARQL Update query to add the SceneObject
        update_query = f"""
        PREFIX ex: <{self.EX}>
        PREFIX xsd: <{XSD}>
        INSERT DATA {{
            <{scene_object_uri}> a ex:SceneObject ;
                            ex:hasType <{object_type_uri}> ;
                            ex:hasVersion "{version}"^^xsd:string ;
                            ex:hasPosition <{position_uri}> ;
                            ex:hasOrientation <{orientation_uri}> .
                            
            <{position_uri}> a ex:Position ;
                            ex:x "{position['x']}"^^xsd:float ;
                            ex:y "{position['y']}"^^xsd:float ;
                            ex:z "{position['z']}"^^xsd:float .
                            
            <{orientation_uri}> a ex:Orientation ;
                            ex:qx "{orientation['qx']}"^^xsd:float ;
                            ex:qy "{orientation['qy']}"^^xsd:float ;
                            ex:qz "{orientation['qz']}"^^xsd:float .
                            ex:qw "{orientation['qw']}"^^xsd:float .
        }}
        """
        
        if DEBUG: print(f"update_query: {update_query}")
        # Run the SPARQL update query to add data
        try:
            self.fuseki_update.run_sparql(update_query)
            print(f"SceneObject {obj_id} inserted successfully!")
        except Exception as e:
            print(f"An error occurred: {e}")

    def get_all_scene_objects(self):
        query = f"""
        PREFIX ex: <{self.EX}>
        SELECT ?sceneObject ?type ?version ?x ?y ?z ?qx ?qy ?qz ?qw
        WHERE {{
            ?sceneObject a ex:SceneObject ;
                        ex:hasType ?type ;
                        ex:hasVersion ?version ;
                        ex:hasPosition ?position ;
                        ex:hasOrientation ?orientation .
            
            ?position ex:x ?x ;
                    ex:y ?y ;
                    ex:z ?z .
            
            ?orientation ex:qx ?qx ;
                         ex:qy ?qy ;
                         ex:qz ?qz ;
                         ex:qw ?qw .
        }}
        """
        
        if DEBUG: print(f"update_query: {query}")

        # Run the SPARQL query and fetch the results
        try:
            query_results = self.fuseki_query.run_sparql(query)
            results = query_results.convert()
            scene_objects = []
            for result in results['results']['bindings']:
                scene_object = {
                    "uri": result['sceneObject']['value'],
                    "type": result['type']['value'],
                    "version": result['version']['value'],
                    "position": {
                        "x": float(result['x']['value']),
                        "y": float(result['y']['value']),
                        "z": float(result['z']['value'])
                    },
                    "orientation": {
                        "qx": float(result['qx']['value']),
                        "qy": float(result['qy']['value']),
                        "qz": float(result['qz']['value']),
                        "qw": float(result['qw']['value']),
                    }
                }
                scene_objects.append(scene_object)
            
            return scene_objects
        except Exception as e:
            print(f"An error occurred: {e}")
            return []

    def get_class_properties(self, g, class_uri):
        properties = []
        # Get all properties that have the given class as their domain
        for s, p, o in g.triples((None, RDFS.domain, class_uri)):
            properties.append(s)
        return properties

    # Function to get the data type or object type of a property
    def get_property_details(self, g, property_uri):
        details = {
            'type': None,
            'range': None,
            'comment': None
        }
        # Get the type of the property
        for s, p, o in g.triples((property_uri, RDF.type, None)):
            details['type'] = o

        # Get the range of the property
        for s, p, o in g.triples((property_uri, RDFS.range, None)):
            details['range'] = o

        # Get any comments or descriptions of the property
        for s, p, o in g.triples((property_uri, RDFS.comment, None)):
            details['comment'] = str(o)

        return details



def main():
    ''' Creates ontology and adds few objects'''
    o = Ontology()
    
    # Add n scene objects dynamically to the Fuseki server
    n = 2  # Define the number of scene objects to add

    for i in range(1, n+1):
        obj_type = "Drawer" if i % 2 == 0 else "Cup"  # Alternate between Drawer and Cup
        version = "Wooden Drawer" if obj_type == "Drawer" else "Ceramic Cup"
        position = {"x": i * 1.0, "y": i * 1.0, "z": i * 1.0}
        orientation = {"qx": i * 0.1, "qy": i * 0.1, "qz": i * 0.1, "qw": i * 0.1}
        
        o.add_scene_object_sparql(obj_id=i, obj_type=obj_type, version=version, position=position, orientation=orientation)

    # Retrieve and print all scene objects and their properties
    scene_objects = o.get_all_scene_objects()
    for obj in scene_objects:
        print(f"SceneObject URI: {obj['uri']}")
        print(f"  Type: {obj['type']}")
        print(f"  Version: {obj['version']}")
        print(f"  Position: x={obj['position']['x']}, y={obj['position']['y']}, z={obj['position']['z']}")
        print(f"  Orientation: qx={obj['orientation']['qx']}, qy={obj['orientation']['qy']}, qz={obj['orientation']['qz']}, qw={obj['orientation']['qw']}")
        print("-" * 50)

if __name__ == "__main__":
    main()