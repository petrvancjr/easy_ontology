from rdflib import Graph, Namespace
from rdflib.namespace import RDF, RDFS, OWL, XSD
from rdflib.namespace import XSD

EX = Namespace("http://example.org/ontology#")

g = Graph()
g.bind("ex", EX)
g.bind("rdf", RDF)
g.bind("rdfs", RDFS)
g.bind("owl", OWL)
g.bind("xsd", XSD)

g.add((EX.SceneObject, RDF.type, OWL.Class))
g.add((EX.Position, RDF.type, OWL.Class))
g.add((EX.Orientation, RDF.type, OWL.Class))
g.add((EX.ObjectType, RDF.type, OWL.Class))  # Class to represent object type (e.g., Drawer, Cup)

# Add Cartesian Position 
g.add((EX.hasPosition, RDF.type, OWL.ObjectProperty))
g.add((EX.hasPosition, RDFS.domain, EX.SceneObject))
g.add((EX.hasPosition, RDFS.range, EX.Position))
for coord in ['x', 'y', 'z']:
    prop = getattr(EX, coord)
    g.add((prop, RDF.type, OWL.DatatypeProperty))
    g.add((prop, RDFS.domain, EX.Position))
    g.add((prop, RDFS.range, XSD.float))

# Add Quaternion Orientation (wrt base)
g.add((EX.hasOrientation, RDF.type, OWL.ObjectProperty))
g.add((EX.hasOrientation, RDFS.domain, EX.SceneObject))
g.add((EX.hasOrientation, RDFS.range, EX.Orientation))
for angle in ['qx', 'qy', 'qz', 'qw']:
    prop = getattr(EX, angle)
    g.add((prop, RDF.type, OWL.DatatypeProperty))
    g.add((prop, RDFS.domain, EX.Orientation))
    g.add((prop, RDFS.range, XSD.float))

# Add Type of the object (drawer, cup, box)
g.add((EX.hasType, RDF.type, OWL.ObjectProperty))
g.add((EX.hasType, RDFS.domain, EX.SceneObject))
g.add((EX.hasType, RDFS.range, EX.ObjectType))  # Property to link SceneObject to ObjectType

# Add Version - Link to 3D model of the object (there can be two different cup models)
# There can be two objects with same version
g.add((EX.hasVersion, RDF.type, OWL.DatatypeProperty))
g.add((EX.hasVersion, RDFS.domain, EX.SceneObject))
g.add((EX.hasVersion, RDFS.range, XSD.string))

# Save the graph to a file
output_file = "scene_objects.owl"
g.serialize(destination=output_file, format='xml')
print(f"Ontology saved to {output_file}")
