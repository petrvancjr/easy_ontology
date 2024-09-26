from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef
from rdflib.namespace import XSD
from pyfuseki import FusekiUpdate, FusekiQuery

from linker import find_link

DEBUG = True

class Ontology():
    # Link to Ontology Software, you probably won't change this
    FUSEKI_URL = 'http://localhost:3030'
    DATASET_NAME = 'mainDataset' # The only dataset used
    BLUEPRINT = 'scene_objects.owl'
    EX = Namespace("http://example.org/ontology#")

    def __init__(self):
        self.g = Graph() # Load the ontology into an RDF graph
        self.g.parse(self.BLUEPRINT, format="xml")
        
        # Load class properties dynamically
        self.property_names_uri = self.get_class_properties(self.EX.SceneObject)
        self.property_names = [property_uri.split("#")[-1] for property_uri in self.property_names_uri.keys()]

        # Modify Scene Objects
        self.fuseki_update = FusekiUpdate(self.FUSEKI_URL, self.DATASET_NAME)
        # Read Scene Object data
        self.fuseki_query = FusekiQuery(self.FUSEKI_URL, self.DATASET_NAME)

    def update(self, objects_data):
        """Update Scene Objects based on new observations

        Args:
            objects_data (List): Format: 
                [
                    { # Object 1
                        "hasType": "Drawer"
                        "hasVersion": "Wooden Drawer"
                        "hasPosition": 
                        "hasOrientation"
                    }, 
                    { ... } # Object 2
                ]
        """
        saved_scene_data = self.get_all_scene_objects() # This might be moved to call less often

        for observed_scene_object in objects_data:
            
            is_link, link_id = find_link(saved_scene_data, observed_scene_object)
            if is_link:
                self.add_scene_object_sparql(link_id, observed_scene_object)
            else:
                self.add_scene_object_sparql(self.get_unique_id(saved_scene_data), observed_scene_object)


    def add_scene_object_sparql(self, obj_id, object_data):
        """Adds a SceneObject using SPARQL update. Constructs a dynamic SPARQL Update query for the SceneObject

        Args:
            obj_id (int): SceneObject Unique id, if already exists, given SceneObject is rewritten
            object_data (dict): {"<properties": <property values>}
        """
        self.verify_scene_object_format(object_data)
        EX = self.EX
        
        object_query_parts = []
        additional_triples = []

        # Iterate over the properties defined in the ontology
        for prop_uri, range_uri in self.property_names_uri.items():
            prop_name = prop_uri.split("#")[-1]

            if prop_name in object_data:
                # Check if the property is an object property (has a class as its range) or a datatype property
                if range_uri.startswith(str(XSD)):  # Datatype property check (e.g., xsd:string, xsd:float)
                    # Handle regular datatype properties
                    object_query_parts.append(f'ex:{prop_name} "{object_data[prop_name]}"^^xsd:{range_uri.split("#")[-1]}')
                else:
                    if isinstance(object_data[prop_name], dict):  # Handling nested properties like Position
                        nested_query = []
                        nested_uri = EX[f"{prop_name}_{obj_id}"]
                        for sub_prop, value in object_data[prop_name].items():
                            # Ensure sub_prop is a property of the nested class (e.g., x, y, z for Position)
                            
                            if EX[prop_name] in self.property_names_uri:
                                nested_query.append(f"ex:{sub_prop} \"{value}\"^^xsd:float ")
                        # Create a triple for the nested property (e.g., Position)
                        nl = " \n\t\t"
                        additional_triples.append(f"<{nested_uri}> a ex:{prop_name} ; \n\t\t {f' ;{nl}'.join(nested_query)} .")
                        # Link the main object to this nested property
                        object_query_parts.append(f"ex:{prop_name} <{nested_uri}>")
                    else:
                        # Handle object properties (with classes as ranges)
                        nested_uri = EX[f"{prop_name}_{obj_id}"]
                        object_query_parts.append(f"ex:{prop_name} <{nested_uri}>")
                        additional_triples.append(f"<{nested_uri}> a ex:{range_uri.split('#')[-1]} .")

        # Combine all parts into the final SPARQL Update query
        nl = " \n\t\t"
        nlc = " ; \n\t\t"
        update_query = f"""
        PREFIX ex: <{EX}>
        PREFIX xsd: <{XSD}>
        INSERT DATA {{
            <{EX[f"SceneObject_{obj_id}"]}> a ex:SceneObject ;
            {nlc.join(object_query_parts)}. {nl}
            {nl.join(additional_triples)}
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
        EX = self.EX
        
        # Construct the SPARQL query dynamically based on the SceneObject properties
        query_parts = []
        nested_properties = {}

        # Prepare the dynamic query parts for known properties
        for prop_uri, range_uri in self.property_names_uri.items():
            prop_name = prop_uri.split("#")[-1]
            
            # Check if this property has nested structure
            if isinstance(range_uri, URIRef) and not str(range_uri).startswith(str(XSD)):
                # Nested object property like hasPosition, hasOrientation
                nested_properties[prop_name] = range_uri
                query_parts.append(f"?sceneObject ex:{prop_name} ?{prop_name}Uri .")
            else:
                # Direct property
                query_parts.append(f"?sceneObject ex:{prop_name} ?{prop_name} .")

        # Add nested properties query parts
        nested_query_parts = []
        nested_select_parts = []
        for nested_prop_name, nested_range_uri in nested_properties.items():
            nested_query = []
            # Get nested properties (like x, y, z for Position)
            for sub_prop_uri in self.get_class_properties(nested_range_uri):
                sub_prop_name = sub_prop_uri.split("#")[-1]
                nested_query.append(f"?{nested_prop_name}Uri ex:{sub_prop_name} ?{nested_prop_name}_{sub_prop_name} .")
                nested_select_parts.append(f"?{nested_prop_name}_{sub_prop_name}")
            nested_query_parts.append(" ".join(nested_query))

        # Combine the query parts
        full_query = f"""
        PREFIX ex: <{EX}>
        PREFIX xsd: <{XSD}>
        SELECT ?sceneObject {' '.join([f'?{prop_uri.split("#")[-1]}' for prop_uri in self.property_names_uri])} {' '.join(nested_select_parts)}
        WHERE {{
            {' '.join(query_parts)}
            {' '.join(nested_query_parts)}
        }}
        """

        # Debug print the query to check for issues
        print("Generated SPARQL Query:")
        print(full_query)

        # Execute the query and process the results
        try:
            query_result = self.fuseki_query.run_sparql(full_query)
            results_dict = query_result.convert()  # Converts to a Python dict
            scene_objects = []
            print("===")
            print(results_dict)
            print("===")
            for result in results_dict['results']['bindings']:
                scene_object = {"uri": result['sceneObject']['value']}

                # Process main object properties
                for prop_uri in self.property_names_uri:
                    prop_name = prop_uri.split("#")[-1]
                    if prop_name in result:
                        if prop_name in nested_properties:
                            # Nested property structure
                            nested_data = {}
                            nested_range_uri = nested_properties[prop_name]
                            for sub_prop_uri in self.get_class_properties(nested_range_uri):
                                sub_prop_name = sub_prop_uri.split("#")[-1]
                                key = f"{prop_name}_{sub_prop_name}"
                                if key in result:
                                    nested_data[sub_prop_name] = float(result[key]['value'])
                            scene_object[prop_name] = nested_data
                        else:
                            # Direct property
                            scene_object[prop_name] = result[prop_name]['value']

                scene_objects.append(scene_object)

            return scene_objects

        except Exception as e:
            print(f"An error occurred while retrieving scene objects: {e}")
            return []

    def get_class_properties(self, class_uri):
        """Get properties of a specific class from the ontology."""
        properties = {}
        # Get all properties that have the given class as their domain
        for prop in self.g.subjects(RDFS.domain, class_uri):
            # Get the range of the property (datatype or object type)
            range_uri = self.g.value(subject=prop, predicate=RDFS.range)
            properties[prop] = range_uri
        return properties

    def verify_scene_object_format(self, object_data):
        assert sorted(list(object_data.keys())) == sorted(self.property_names), \
            f"Properties do not match, {sorted(list(object_data.keys()))} != {sorted(self.property_names)}"

    def get_unique_id(self, saved_scene_data):
        pass

def main():
    o = Ontology()
    
    # We observe some objects (get their class, position, orientation, etc.)
    scene_objects_data = []
    for i in range(1, 5):
        object_data = {
            'hasType': "Drawer" if i % 2 == 0 else "Cup",  # Alternate between Drawer and Cup
            'hasVersion': "Wooden Drawer" if i % 2 == 0 else "Ceramic Cup",
            'hasPosition': {"x": i * 1.0, "y": i * 1.0, "z": i * 1.0},
            'hasOrientation': {"qx": i * 0.1, "qy": i * 0.1, "qz": i * 0.1, "qw": i * 0.1},
        }    
    scene_objects_data.append(object_data)
    
    # Then we update the ontology with the data
    o.update(scene_objects_data)
    
    # Finally, retrieve and print all scene objects and their properties
    scene_objects = o.get_all_scene_objects()
    print(scene_objects)
    for obj in scene_objects:
        print(f"SceneObject URI: {obj['uri']}")
        print(f"  Type: {obj['type']}")
        print(f"  Version: {obj['version']}")
        print(f"  Position: x={obj['position']['x']}, y={obj['position']['y']}, z={obj['position']['z']}")
        print(f"  Orientation: qx={obj['orientation']['qx']}, qy={obj['orientation']['qy']}, qz={obj['orientation']['qz']}, qw={obj['orientation']['qw']}")
        print("-" * 50)

if __name__ == "__main__":
    main()