from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL, XSD

class Ontology():
    def initialize_classes(self):
        # Define the namespace
        EX = Namespace("http://example.org/ontology#")

        # Create an RDF graph
        g = Graph()
        g.bind("ex", self.EX)
        g.bind("rdf", self.RDF)
        g.bind("rdfs", self.RDFS)
        g.bind("owl", self.OWL)
        g.bind("xsd", self.XSD)

        # Define ontology classes
        g.add((self.EX.SceneObject, RDF.type, OWL.Class))
        g.add((self.EX.Position, RDF.type, OWL.Class))
        g.add((self.EX.Orientation, RDF.type, OWL.Class))
        g.add((self.EX.ObjectType, RDF.type, OWL.Class))  # Class to represent object type (e.g., Drawer, Cup)

        # Define properties
        g.add((self.EX.hasPosition, RDF.type, OWL.ObjectProperty))
        g.add((self.EX.hasPosition, RDFS.domain, EX.SceneObject))
        g.add((self.EX.hasPosition, RDFS.range, EX.Position))

        g.add((self.EX.hasOrientation, RDF.type, OWL.ObjectProperty))
        g.add((self.EX.hasOrientation, RDFS.domain, EX.SceneObject))
        g.add((self.EX.hasOrientation, RDFS.range, EX.Orientation))

        g.add((self.EX.hasType, RDF.type, OWL.ObjectProperty))
        g.add((self.EX.hasType, RDFS.domain, EX.SceneObject))
        g.add((self.EX.hasType, RDFS.range, EX.ObjectType))  # Property to link SceneObject to ObjectType

        g.add((self.EX.hasVersion, RDF.type, OWL.DatatypeProperty))
        g.add((self.EX.hasVersion, RDFS.domain, EX.SceneObject))
        g.add((self.EX.hasVersion, RDFS.range, XSD.string))

        # Define Position properties
        for coord in ['x', 'y', 'z']:
            prop = getattr(EX, coord)
            g.add((prop, RDF.type, OWL.DatatypeProperty))
            g.add((prop, RDFS.domain, EX.Position))
            g.add((prop, RDFS.range, XSD.float))

        # Define Orientation properties
        for angle in ['roll', 'pitch', 'yaw']:
            prop = getattr(EX, angle)
            g.add((prop, RDF.type, OWL.DatatypeProperty))
            g.add((prop, RDFS.domain, EX.Orientation))
            g.add((prop, RDFS.range, XSD.float))
        return g 

    # Function to add a SceneObject to the graph
    def add_scene_object(self, graph, obj_id, obj_type, version, position, orientation):
        # Create URIs for the SceneObject and its properties
        scene_object_uri = self.EX[f"SceneObject_{obj_id}"]
        position_uri = self.EX[f"Position_{obj_id}"]
        orientation_uri = self.EX[f"Orientation_{obj_id}"]
        object_type_uri = self.EX[obj_type]

        # Add the SceneObject
        graph.add((scene_object_uri, RDF.type, self.EX.SceneObject))
        graph.add((scene_object_uri, self.EX.hasType, object_type_uri))
        graph.add((scene_object_uri, self.EX.hasVersion, Literal(version, datatype=XSD.string)))

        # Add the position
        graph.add((position_uri, RDF.type, self.EX.Position))
        graph.add((position_uri, self.EX.x, Literal(position['x'], datatype=XSD.float)))
        graph.add((position_uri, self.EX.y, Literal(position['y'], datatype=XSD.float)))
        graph.add((position_uri, self.EX.z, Literal(position['z'], datatype=XSD.float)))
        graph.add((scene_object_uri, self.EX.hasPosition, position_uri))

        # Add the orientation
        graph.add((orientation_uri, RDF.type, self.EX.Orientation))
        graph.add((orientation_uri, self.EX.roll, Literal(orientation['roll'], datatype=XSD.float)))
        graph.add((orientation_uri, self.EX.pitch, Literal(orientation['pitch'], datatype=XSD.float)))
        graph.add((orientation_uri, self.EX.yaw, Literal(orientation['yaw'], datatype=XSD.float)))
        graph.add((scene_object_uri, self.EX.hasOrientation, orientation_uri))


def main():
    ''' Creates ontology and adds few objects'''
    o = Ontology()
    g = o.initialize_classes()
    
    # Add n scene objects
    n = 5  # Define the number of scene objects to add

    for i in range(1, n+1):
        obj_type = "Drawer" if i % 2 == 0 else "Cup"  # Alternate between Drawer and Cup
        version = "Wooden Drawer" if obj_type == "Drawer" else "Ceramic Cup"
        position = {"x": i * 1.0, "y": i * 1.0, "z": i * 1.0}
        orientation = {"roll": i * 0.1, "pitch": i * 0.1, "yaw": i * 0.1}
        
        o.add_scene_object(g, obj_id=i, obj_type=obj_type, version=version, position=position, orientation=orientation)

    # Save the graph to a file
    output_file = "scene_objects.owl"
    g.serialize(destination=output_file, format='xml')
    print(f"Ontology saved to {output_file}")

if __name__ == "__main__":
    main()