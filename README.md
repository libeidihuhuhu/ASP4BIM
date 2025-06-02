# ASP4BIM
A declarative spatial reasoning system based on Answer Set Programming (ASP) to query, analyse, validate, and optimise large-scale Building Information Models (BIM).

# Background
ASP4BIM is a logic-based reasoning framework specifically designed for implicit, incomplete human spatial knowledge and numerous, complex real-world spatial data.

ASP4BIM can be viewed as a melting pot for 
* natural language statements describing a person's experiences and behaviour in the built environment that are often ambiguous and vague by nature, 
* digital building models with rich semantics and complex geometries that are posssibly inaccurate and imprecise, 
* domain-specific rules and constraints about human-centric design concepts such as privacy, accessibility, safety, navigability, audibility, etc.

<p align="center">
  <img width="700" src="/ASP4BIM_conceptual_framework.png">
</p>

# Dependencies
ASP4BIM is implemented via `clingo`'s Python API (https://potassco.org/clingo/python-api/5.4/) and uses state-of-the-art geometry libraries for spatial computations.

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

# Example queries

# Acknowledgements
ASP4BIM is currently being developed within the scope of my PhD project [Intelligent Software, Healing Environment](https://digit.au.dk/research-projects/intelligent-software-healing-environments/) at the Cyber-Physical Systems group, Aarhus University, Denmark. ASP4BIM is largely based on prototype systems [CLP(QS)](https://hub.docker.com/r/spatialreasoning/clpqs) and [ASPMT(QS)](https://hub.docker.com/r/spatialreasoning/aspmtqs), and draws from many theoretical and practical contributions of the modern ASP system `clingo`.  

The data used in the source codes, courtesy of Assoc.Prof. Jochen Teizer, Dr. Olga Golovina, and Asst.Prof. Aliakbar Kamari, are for demonstration purposes only and strictly proprietary. I am also extremely grateful to my supervisors Asst.Prof. Carl Schultz and Prof. Peter Gorm Larsen for their guidance, and the Independent Research Fund Denmark (DFF) for their financial support.

# References
Please kindly refer to the following research papers for a deep-dive into Declarative Spatial Reasoning, Answer Set Programming, and Building Information Modelling. 

[1] Gebser, M., Kaminski, R., Kaufmann, B., Ostrowski, M., Schaub, T., & Wanko, P. (2016). *Theory solving made easy with clingo 5*. In *Technical Communications of the 32nd International Conference on Logic Programming (ICLP 2016)*. Open Access Series in Informatics (OASIcs). Schloss Dagstuhl–Leibniz-Zentrum für Informatik. [https://doi.org/10.4230/OASIcs.ICLP.2016.2](https://doi.org/10.4230/OASIcs.ICLP.2016.2)

[2] Li, B., & Schultz, C. (2024). *Clingo2DSR – A clingo-based software system for declarative spatial reasoning*. *Spatial Cognition & Computation*, 25(1), 69–119. [https://doi.org/10.1080/13875868.2024.2324875](https://doi.org/10.1080/13875868.2024.2324875)





