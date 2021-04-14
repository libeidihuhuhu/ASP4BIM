# ASP4BIM
A declarative spatial reasoning system based on Answer Set Programming for querying, analysing, and checking large-scale Building Information Models

# Background
ASP4BIM is a logic-based reasoning framework specifically designed for implicit, incomplete human spatial knowledge and numerous, complex real-world spatial data  

ASP4BIM can be viewed as a melting pot for 
* natural language statements describing a person's experiences and behaviour in the built environment that are ambiguous and vague by nature
* a building model with semantic and geometric information that are posssibly inaccurate and imprecise
* domain-specific rules and constraints about human-centric design concepts such as privacy, accessibility, safety, navigability, audibility, etc.



ASP is implemented via clingo's Python API and uses state-of-the-art geometry libraries for spatial computations

# Dependencies
1. Install [clingo](https://potassco.org/doc/start/) via `conda`  
```
conda install -c potassco clingo
```  
We use clingo version 5.4.0 with Python 3.7.4  


