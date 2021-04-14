# ASP4BIM
A declarative spatial reasoning system based on Answer Set Programming for querying, analysing, and checking large-scale Building Information Models

# Background
ASP4BIM is a logic-based reasoning framework specifically designed for implicit, incomplete human spatial knowledge and numerous, complex real-world spatial data  

ASP4BIM can be viewed as a melting pot for 
* natural language statements describing a person's experiences and behaviour in the built environment that are often ambiguous and vague by nature
* a building model with semantic and geometric information that are posssibly inaccurate and imprecise
* domain-specific rules and constraints about human-centric design concepts such as privacy, accessibility, safety, navigability, audibility, etc.

<p align="center">
  <img width="700" src="/ASP4BIM_conceptual_framework.png">
</p>

# Dependencies
ASP4BIM is implemented via clingo's Python API (https://potassco.org/clingo/python-api/5.4/) and uses state-of-the-art geometry libraries for spatial computations  

1. Install [clingo](https://potassco.org/doc/start/) via `conda`  
```
conda install -c potassco clingo
```  
We use clingo version 5.4.0 with Python 3.7.4

2. We use [Clipper](http://www.angusj.com/delphi/clipper.php) to compute Boolean operations on polygons  
Install the Python wrapper via pip
```
pip install pyclipper
```
Alternatively, one can use [PyMesh](https://pymesh.readthedocs.io/en/latest/) for polyhedrons

# Acknowledgements
ASP4BIM is currently being developed within the scope of my PhD project [Intelligent Software, Healing Environment](https://digit.au.dk/research-projects/intelligent-software-healing-environments/) at the Cyber-Physical Systems group, Aarhus University, Denmark. ASP4BIM is largely based on prototype systems [CLP(QS)](https://hub.docker.com/r/spatialreasoning/clpqs) and [ASPMT(QS)](https://hub.docker.com/r/spatialreasoning/aspmtqs), and draws from many theoretical and practical contributions of the modern ASP system `clingo`.  

The data used in the source codes are by courtesy of Assoc.Prof. Jochen Teizer, Dr. Olga Golovina, and Asst.Prof. Aliakbar Kamari, thus for demonstration purposes only and strictly proprietary. I am also extremely grateful to my supervisors Asst.Prof. Carl Schultz and Prof. Peter Gorm Larsen for their guidance, and the Danish Independent Research Fund Denmark (DFF) for their financial support.

Please kindly refer to the following research papers for an overview of Declarative Spatial Reasoning, Answer Set Programming, and Building Information Modelling  






